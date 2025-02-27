# Updated System Architecture & Technical Specification

## 1. Core Architecture

### 1.1 Design Principles
1. **Data Ownership**
   - All data stored locally
   - Clear separation of system and user data
   - Transparent data organization

2. **Architectural Clarity**
   - Clear separation of concerns
   - Modular components
   - Explicit dependencies
   - Type safety throughout

3. **User Experience**
   - Responsive interface
   - Efficient image loading
   - Intuitive generation workflow
   - Simple organization options

4. **Operational Simplicity**
   - Flexible deployment (local or remote InvokeAI)
   - Simple backup strategy
   - Clear error handling
   - Manageable dependencies

### 1.2 Deployment Modes

The application supports two deployment modes for InvokeAI integration:

1. **Local Mode**
   - InvokeAI runs on the same machine as the application
   - API accessed via localhost (e.g., `http://localhost:9090`)
   - Lower latency, no network dependencies
   - Direct cost control (system resources only)

2. **Remote Mode**
   - InvokeAI runs on RunPod or similar service
   - API accessed via HTTPS (e.g., `https://{pod-id}-9090.proxy.runpod.net`)
   - On-demand resource scaling
   - Usage-based cost model

Both modes use the same API-based integration approach, with no direct file system dependencies. The application treats both modes identically except for connection management.

## 2. Technical Infrastructure

### 2.1 Database Architecture

#### Core Photo Management
```sql
CREATE TABLE photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL UNIQUE,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Generation metadata (null for uploaded photos)
    is_generated BOOLEAN DEFAULT FALSE,
    generation_prompt TEXT,
    generation_params JSONB,
    source_image_id UUID REFERENCES photos(id),
    
    -- System metadata
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Remote retrieval tracking
    remote_backend_url TEXT,
    remote_image_id TEXT,
    retrieval_status TEXT DEFAULT 'completed' 
        CHECK (retrieval_status IN ('pending', 'completed', 'failed')),
    local_storage_path TEXT,
    local_thumbnail_path TEXT
);

CREATE TABLE albums (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    cover_photo_id UUID REFERENCES photos(id)
);

CREATE TABLE album_photos (
    album_id UUID REFERENCES albums(id),
    photo_id UUID REFERENCES photos(id),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    position INTEGER,
    PRIMARY KEY (album_id, photo_id)
);

CREATE TABLE shared_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    photo_id UUID REFERENCES photos(id),
    album_id UUID REFERENCES albums(id),
    access_key TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT share_target_check 
        CHECK (
            (photo_id IS NOT NULL AND album_id IS NULL) OR
            (photo_id IS NULL AND album_id IS NOT NULL)
        )
);
```

#### Generation Workflow Management
```sql
CREATE TABLE generation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    entry_type TEXT NOT NULL CHECK (entry_type IN ('scratch', 'refinement')),
    source_image_id UUID REFERENCES photos(id),
    status TEXT NOT NULL DEFAULT 'active' 
        CHECK (status IN ('active', 'completed', 'abandoned'))
);

CREATE TABLE generation_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES generation_sessions(id),
    parent_id UUID REFERENCES generation_steps(id),
    prompt TEXT NOT NULL,
    negative_prompt TEXT,
    parameters JSONB NOT NULL,
    model_id TEXT NOT NULL,
    batch_id TEXT NOT NULL,
    selected_image_id UUID REFERENCES photos(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    position INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

CREATE TABLE step_alternatives (
    step_id UUID NOT NULL REFERENCES generation_steps(id),
    image_id UUID NOT NULL REFERENCES photos(id),
    selected BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (step_id, image_id)
);

CREATE TABLE generation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_photo_id UUID REFERENCES photos(id),
    result_photo_id UUID REFERENCES photos(id),
    prompt TEXT NOT NULL,
    negative_prompt TEXT,
    parameters JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 File System Organization

```
/data
  └── photos/                        # Main photo directory
      ├── generated/                 # AI-generated images
      │   ├── sessions/              # Organized by generation session
      │   │   └── {session_id}/      # Contains all images from a session
      │   │       └── {step_id}/     # Further organized by step
      │   │           ├── selected/  # Contains selected images
      │   │           └── variants/  # Contains alternative variations
      │   └── completed/             # Final selected images (flat organization)
      │       └── {yyyy-mm-dd}/      # Organized by date
      ├── uploaded/                  # User uploads
      │   └── {yyyy-mm-dd}/          # Organized by date
      └── thumbnails/                # All thumbnails (WebP format)
          ├── generated/             # Mirrors generated structure
          │   ├── sessions/          # Same session-based structure
          │   └── completed/         # Same date-based structure
          └── uploaded/              # Mirrors uploaded structure
              └── {yyyy-mm-dd}/      # Same date-based structure
```

### 2.3 Service Layer

#### Core Photo Services
```python
class PhotoService:
    async def create(self, file: UploadFile) -> Photo
    async def get(self, id: UUID) -> Optional[Photo]
    async def list(self, filters: PhotoFilters) -> List[Photo]
    async def delete(self, id: UUID) -> bool

class AlbumService:
    async def create(self, data: AlbumCreate) -> Album
    async def add_photos(self, id: UUID, photo_ids: List[UUID]) -> bool
    async def remove_photos(self, id: UUID, photo_ids: List[UUID]) -> bool

class ShareService:
    async def create_share_link(self, photo_id: UUID, expires_in: Optional[timedelta]) -> str
    async def get_shared_photo(self, access_key: str) -> Optional[Photo]
```

#### Generation Services
```python
class InvokeAIClient:
    """Client for interacting with InvokeAI API, handling complex graph-based requests and response processing."""
    
    # Connection management
    async def connect(self, base_url: str) -> bool
    async def get_api_version(self) -> str
    async def check_health(self) -> bool
    
    # Model management
    async def get_models(self, refresh_cache: bool = False) -> List[Model]
    async def find_compatible_vae(self, model_key: str) -> Optional[Model]
    
    # Graph construction
    def create_generation_graph(self, parameters: GenerationParameters) -> Dict
    def validate_graph(self, graph: Dict) -> Tuple[bool, Optional[str]]
    
    # Generation flow
    async def queue_generation(self, parameters: GenerationParameters) -> BatchResponse
    async def get_batch_status(self, batch_id: str) -> BatchStatus
    async def wait_for_batch_completion(self, batch_id: str, timeout_seconds: int = 300) -> BatchResult
    
    # Image retrieval
    async def list_recent_images(self, limit: int, since: Optional[datetime] = None) -> List[ImageInfo]
    async def get_image(self, image_name: str) -> bytes
    async def get_thumbnail(self, image_name: str) -> bytes
    async def get_image_metadata(self, image_name: str) -> Dict
    
    # Clean-up operations
    async def delete_image(self, image_name: str) -> bool
    
    # Cache and helper methods
    def _build_model_cache(self, models_data: Dict) -> None
    def _create_unique_node_id(self, prefix: str) -> str
    
class GenerationSessionService:
    """Manages generation sessions and their lifecycle."""
    
    async def create_session(self, 
                            entry_type: str, 
                            source_image_id: Optional[UUID]) -> GenerationSession
    
    async def get_session(self, id: UUID) -> Optional[GenerationSession]
    async def list_sessions(self, limit: int, offset: int, status: Optional[str] = None) -> List[GenerationSession]
    async def complete_session(self, id: UUID) -> bool
    async def abandon_session(self, id: UUID) -> bool
    async def delete_session(self, id: UUID) -> bool
    
    # New methods
    async def get_session_history(self, id: UUID) -> SessionHistory
    async def get_latest_image(self, id: UUID) -> Optional[Photo]
    async def get_session_statistics(self, id: UUID) -> SessionStats
    
class GenerationStepService:
    """Manages individual generation steps within a session."""
    
    async def create_step(self, 
                         session_id: UUID, 
                         request: StepRequest, 
                         correlation_id: Optional[str] = None) -> GenerationStep
    
    async def get_step(self, id: UUID) -> Optional[GenerationStep]
    async def get_step_status(self, id: UUID) -> StepStatus
    async def select_alternative(self, step_id: UUID, image_id: UUID) -> bool
    async def get_step_alternatives(self, step_id: UUID) -> List[StepAlternative]
    async def get_session_steps(self, session_id: UUID) -> List[GenerationStep]
    
    # New methods
    async def cancel_step(self, id: UUID) -> bool
    async def get_step_lineage(self, id: UUID) -> List[GenerationStep]
    async def retry_failed_step(self, id: UUID) -> Optional[GenerationStep]
    async def retry_step_retrievals(self, id: UUID) -> RetrievalStatus

class ImageRetrievalService:
    """Service for retrieving, correlating, and storing generated images from InvokeAI."""
    
    # Core retrieval methods
    async def retrieve_batch_images(self, 
                                   batch_id: str, 
                                   expected_count: int, 
                                   session_id: UUID, 
                                   step_id: UUID,
                                   correlation_id: Optional[str] = None) -> RetrievalResult
    
    async def retrieve_single_image(self, 
                                   image_name: str, 
                                   session_id: UUID, 
                                   step_id: UUID) -> Optional[Photo]
    
    # Correlation strategies
    async def _correlate_images_by_timestamp(self, 
                                           batch_completion_time: datetime, 
                                           expected_count: int) -> List[str]
    
    async def _correlate_images_by_id(self, 
                                     correlation_id: str,
                                     expected_count: int) -> List[str]
    
    # Retry mechanisms
    async def retry_failed_retrievals(self, step_id: Optional[UUID] = None) -> Dict[str, int]
    async def retry_specific_retrievals(self, photo_ids: List[UUID]) -> Dict[str, int]
    
    # Status management
    async def get_retrieval_status(self, step_id: UUID) -> RetrievalStatus
    
    # Storage operations
    async def _store_image(self, 
                          image_data: bytes, 
                          thumbnail_data: bytes,
                          metadata: Dict, 
                          session_id: UUID, 
                          step_id: UUID) -> Photo
    
    async def _organize_files(self, 
                             session_id: UUID, 
                             step_id: UUID, 
                             is_selected: bool = False) -> Tuple[str, str]

class ModelManagementService:
    """Service for managing InvokeAI model information and caching."""
    
    async def get_available_models(self, refresh_cache: bool = False) -> List[Model]
    async def get_model_by_key(self, key: str) -> Optional[Model]
    async def get_compatible_vaes(self, model_key: str) -> List[Model]
    async def get_default_parameters(self, model_key: str) -> Dict
    async def refresh_model_cache(self) -> bool
    async def add_model_to_favorites(self, model_key: str) -> bool
    async def remove_model_from_favorites(self, model_key: str) -> bool
    async def get_favorite_models(self) -> List[Model]

```

#### Connection Management
```python
class BackendConnectionManager:
    async def get_backend_url() -> str
    async def test_connection(url: str) -> bool
    async def switch_mode(use_remote: bool) -> bool
    
class RunPodManager:
    async def start_pod() -> Dict
    async def stop_pod(pod_id: str) -> bool
    async def get_status(pod_id: str) -> PodStatus
    async def get_cost_metrics(pod_id: str) -> CostMetrics
```

#### Server Storage
```python
def generate_storage_paths(session_id: UUID, step_id: UUID, image_id: str, is_selected: bool = False) -> Dict[str, str]:
    """Generate file paths for storing retrieved images from InvokeAI."""
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Session-based paths (for active workflow)
    session_path = f"data/photos/generated/sessions/{session_id}/{step_id}"
    session_sub_path = "selected" if is_selected else "variants"
    session_full_path = f"{session_path}/{session_sub_path}/{image_id}.png"
    session_thumb_path = f"data/photos/thumbnails/generated/sessions/{session_id}/{step_id}/{session_sub_path}/{image_id}.webp"
    
    # Completed paths (for selected images)
    completed_path = f"data/photos/generated/completed/{today}/{image_id}.png"
    completed_thumb_path = f"data/photos/thumbnails/generated/completed/{today}/{image_id}.webp"
    
    return {
        "session_full_path": session_full_path,
        "session_thumb_path": session_thumb_path,
        "completed_full_path": completed_path if is_selected else None,
        "completed_thumb_path": completed_thumb_path if is_selected else None
    }
```

## 3. Key Workflows

### 3.1 Generation Workflow

The application implements a linear history model with alternatives:

1. Session Creation
   - User starts a new generation session
   - System creates a generation_sessions record
   
2. Model Selection
   - User selects a model from available models
   - System retrieves compatible VAEs and default parameters
   - System presents parameter suggestions to user
   
3. Step Creation
   - User configures prompt and parameters
   - System generates a correlation ID for tracking
   - System creates a generation_steps record
   - System constructs the graph-based request:
     - Creates all required nodes (model_loader, prompt, noise, etc.)
     - Sets up all edges between nodes
     - Populates metadata in both nodes and data section
   - System submits request to InvokeAI queue
   - System receives batch ID
   
4. Status Monitoring
   - System polls batch status with exponential backoff
   - System updates step status based on batch status
   - System provides progress information to user
   
5. Image Retrieval
   - On batch completion, system initiates image retrieval:
     - Queries recent images by timestamp
     - Verifies count matches batch size
     - Downloads full images, thumbnails, and metadata
     - Stores files in appropriate locations
     - Creates database records
     - Updates retrieval status
   
6. Alternative Selection
   - User selects one image as preferred
   - System marks the selection in step_alternatives
   - System copies selected image to completed folder (optional)
   
7. Continuation or Completion
   - User can either:
     - Create a new step based on selection
     - Complete the session
   - System updates status and performs cleanup

### 3.2 Image Retrieval Process

1. Batch Completion Detection
   - System detects batch completion through polling
   - System records exact completion timestamp
   
2. Image Correlation
   - System uses one of these strategies:
     a. Timestamp-based: Retrieve images created after batch start
     b. ID-based: Verify correlation ID in metadata
     c. Count-based: Retrieve exactly the expected number of images
   
3. Parallel Retrieval
   - For each correlated image:
     - Create retrieval job with pending status
     - Download full image, thumbnail, and metadata concurrently
     - Store files in session/step folder structure
     - Create photo database record with generation metadata
     - Update retrieval status to completed
   
4. Error Handling
   - For connection errors:
     - Implement retry with exponential backoff
     - Mark retrieval as failed after max attempts
   - For partial retrievals:
     - Continue with successfully retrieved images
     - Mark failed retrievals for background retry
   
5. Status Reporting
   - Provide real-time retrieval status to user
   - Show progress indicators for ongoing retrievals
   - Offer manual retry options for failed retrievals
   
6. Background Recovery
   - Scheduled job checks for failed retrievals
   - Implements longer-term retry strategy
   - Updates database status on completion

### 3.3 Remote Backend Management

For remote mode only:

1. Pod Management
   - User selects remote mode
   - System checks for existing pod:
     - If running: Connect to existing pod
     - If stopped: Start pod via RunPod API
     - If non-existent: Create new pod
   
2. Model Management
   - System queries available models from remote pod
   - System caches model information locally
   - System maps model keys and hashes for future requests
   
3. Activity Monitoring
   - System tracks last activity timestamp
   - System calculates idle time
   - After configurable idle threshold:
     - System warns user of impending shutdown
     - User can extend session or allow shutdown
     - System stops pod via RunPod API
   
4. Cost Tracking
   - System calculates session duration
   - System estimates cost based on pod type
   - System provides cost visualization to user
   - System maintains cost history for budgeting
   
5. Failure Recovery
   - System detects pod failures
   - System offers restart options
   - System recovers session state if possible

## 4. Implementation Guidelines

### 4.1 Development Environment
- Local Python environment
- Direct database access
- Local or remote InvokeAI instance
- Simple configuration files

### 4.2 Error Handling
- Specific error types for different failure modes
- Exponential backoff for immediate retries
- Scheduled retry for persistent failures
- User feedback for ongoing recovery attempts

### 4.3 Performance Considerations
- Efficient image retrieval and storage
- Background processing for retrieval and cleanup
- Caching strategy for frequently accessed images
- Batch operations for improved efficiency

### 4.4 Backup Strategy
- Regular database backups
- Image directory backups
- Configuration backups
- Simple recovery procedures

## 5. Deployment

### 5.1 Requirements
- Local machine installation
- PostgreSQL database
- Python runtime
- Local InvokeAI instance (optional)
- RunPod API access (for remote mode)

### 5.2 Configuration
- Environment variables
- Database connection
- Storage paths
- InvokeAI settings
- RunPod API key (for remote mode)

```python
# InvokeAI Integration Configuration
INVOKEAI_CONNECTION_TIMEOUT = 10  # seconds
INVOKEAI_READ_TIMEOUT = 30  # seconds
INVOKEAI_BATCH_STATUS_INTERVAL = 2  # seconds
INVOKEAI_MODEL_CACHE_TTL = 900  # 15 minutes
INVOKEAI_MAX_BATCH_SIZE = 10
INVOKEAI_MAX_RETRIES = 5
INVOKEAI_RETRY_DELAY = 2  # seconds

# Remote Pod Configuration  
RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY")
RUNPOD_POD_TYPE = "NVIDIA A5000"
RUNPOD_IDLE_TIMEOUT = 30  # minutes
```

### 5.3 Monitoring
- Local logging
- Resource monitoring
- Storage tracking
- Error reporting
- Cost monitoring (remote mode)

### 5.4 Background Tasks
```python
# Background task registration
background_tasks = [
    # Run every minute
    ("retry_pending_retrievals", 60, image_retrieval_service.retry_pending_retrievals),
    
    # Run every 15 minutes
    ("refresh_model_cache", 900, model_management_service.refresh_model_cache),
    
    # Run every 5 minutes
    ("check_pod_idle", 300, backend_manager.check_pod_idle_status)
]
```

## 6. Security

```python
# Security validation for InvokeAI interaction
def validate_model_access(model_key: str, user_id: UUID) -> bool:
    """Validate if a user has access to the specified model."""
    # Single-user system always returns True
    return True

def validate_generation_parameters(params: Dict) -> Tuple[bool, Optional[str]]:
    """Validate generation parameters for security and resource constraints."""
    # Validate dimensions
    if params.get("width", 0) * params.get("height", 0) > 1920 * 1080:
        return False, "Image dimensions too large"
        
    # Validate batch size
    if params.get("batch_size", 1) > 10:
        return False, "Batch size too large"
        
    # Validate steps
    if params.get("steps", 0) > 50:
        return False, "Step count too large"
        
    return True, None
```

### 6.1 Share Links
- Unique access keys
- Optional expiration
- Simple validation
- Access tracking

### 6.2 Local Security
- File permissions
- Database access
- Configuration protection
- Backup security

### 6.3 Remote Access
- Secure API access
- RunPod API key protection
- No authentication for InvokeAI API (as per requirements)
- Network isolation where possible