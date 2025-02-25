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
  └── photos/                    # Main photo directory
      ├── generated/             # AI-generated images
      │   ├── sessions/          # Organized by generation session
      │   │   └── {session_id}/  # Contains all images from a session
      │   │       └── {step_id}/ # Further organized by step
      │   └── alternatives/      # Stores unselected variations
      ├── uploaded/              # User uploads
      └── thumbnails/            # All thumbnails (WebP format)
          ├── generated/         # Mirrors generated structure
          └── uploaded/          # Mirrors uploaded structure
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
    async def connect(self, base_url: str) -> bool
    async def get_models(self) -> List[Model]
    async def queue_generation(self, request: GenerationRequest) -> BatchResponse
    async def get_batch_status(self, batch_id: str) -> BatchStatus
    async def get_image(self, image_id: str) -> bytes
    async def get_thumbnail(self, image_id: str) -> bytes
    async def get_metadata(self, image_id: str) -> Dict
    
class GenerationSessionService:
    async def create_session(self, entry_type: str, source_image_id: Optional[UUID]) -> GenerationSession
    async def get_session(self, id: UUID) -> Optional[GenerationSession]
    async def complete_session(self, id: UUID) -> bool
    async def abandon_session(self, id: UUID) -> bool
    
class GenerationStepService:
    async def create_step(self, session_id: UUID, request: StepRequest) -> GenerationStep
    async def select_alternative(self, step_id: UUID, image_id: UUID) -> bool
    async def get_step_alternatives(self, step_id: UUID) -> List[StepAlternative]
    async def get_session_steps(self, session_id: UUID) -> List[GenerationStep]

class ImageRetrievalService:
    async def retrieve_and_store(self, backend_url: str, image_id: str, session_id: UUID, step_id: UUID) -> Photo
    async def retry_failed_retrievals() -> Dict[str, int]  # Returns counts of success/failure
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

## 3. Key Workflows

### 3.1 Generation Workflow

The application implements a linear history model with alternatives:

1. **Session Creation**
   - User starts a new generation session (from scratch or from existing image)
   - System creates a `generation_sessions` record

2. **Step Creation**
   - User configures prompt and parameters
   - System creates a `generation_steps` record
   - InvokeAI generates a batch of images (1-10)
   - System retrieves and stores images

3. **Alternative Selection**
   - User selects one image as the "canon" choice for this step
   - System marks the selection in `step_alternatives`
   - Non-selected alternatives remain accessible but not part of the main timeline

4. **Continuation**
   - User can modify prompts and create a new step
   - New step references the previous step as its parent

5. **Reversion**
   - User can revert to any previous step
   - System deletes or marks as invalid all subsequent steps
   - User can select a different alternative and create a new branch

6. **Completion**
   - User completes the session
   - System updates status and performs cleanup

### 3.2 Image Retrieval Process

For both local and remote modes:

1. **Generation Request**
   - Application sends generation request to InvokeAI
   - InvokeAI returns a batch ID

2. **Status Monitoring**
   - Application polls status until generation is complete
   - On completion, InvokeAI provides image IDs

3. **Image Retrieval**
   - For each image ID:
     - Retrieve full image via API
     - Retrieve thumbnail via API
     - Retrieve metadata via API
   - Store images in the appropriate local directory
   - Create database records with local paths

4. **Error Handling**
   - On network failures, implement retry mechanism
   - For persistent failures, mark retrieval as failed
   - Provide UI feedback and manual retry options

### 3.3 Remote Backend Management

For remote mode only:

1. **Pod Startup**
   - User initiates generation in remote mode
   - System checks if pod is running
   - If not, system starts pod via RunPod API
   - System waits for pod to become available

2. **Activity Monitoring**
   - System tracks last activity timestamp
   - After 30 minutes of inactivity, system stops pod
   - Cost metrics are updated and displayed to user

3. **Cost Tracking**
   - System calculates current session cost
   - Displays cost information in UI
   - Provides shutdown option to control costs

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

### 5.3 Monitoring
- Local logging
- Resource monitoring
- Storage tracking
- Error reporting
- Cost monitoring (remote mode)

## 6. Security

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