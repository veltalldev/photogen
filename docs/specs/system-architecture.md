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
    
    def __init__(self, 
                model_cache_service: ModelManagementService,
                connection_timeout: int = 10, 
                read_timeout: int = 30):
        """
        Initialize the InvokeAI client.
        
        Args:
            model_cache_service: Service for model information
            connection_timeout: Timeout for establishing connections (seconds)
            read_timeout: Timeout for reading responses (seconds)
        """
        self.base_url = None  # Set during connect()
        self.model_cache_service = model_cache_service
        self.graph_builder = GraphBuilder(model_cache_service)  # Use the GraphBuilder
        self.timeout = httpx.Timeout(connect=connection_timeout, read=read_timeout)
        self.connected = False
        self.api_version = None
        self._http_client = None  # Will be initialized during connect()
    
    # Connection management
    async def connect(self, base_url: str) -> bool:
        """
        Connect to InvokeAI API at the specified URL.
        
        Handles both local connections (http://localhost:9090) and
        remote RunPod connections (https://{pod-id}-9090.proxy.runpod.net).
        
        Args:
            base_url: The base URL for the InvokeAI API
            
        Returns:
            bool: True if connection successful
        """
        self.base_url = base_url
        
        # Close existing client if any
        if self._http_client:
            await self._http_client.aclose()
        
        # Create new client with appropriate settings
        self._http_client = httpx.AsyncClient(
            timeout=self.timeout,
            base_url=self.base_url,
            # Add additional settings for SSL in case of RunPod
            verify=True if base_url.startswith("https") else False,
            follow_redirects=True
        )
        
        try:
            # Test connection
            version = await self.get_api_version()
            if version:
                self.connected = True
                self.api_version = version
                return True
            return False
        except Exception as e:
            self.connected = False
            self.api_version = None
            print(f"Connection error: {e}")
            return False
    
    async def get_api_version(self) -> str:
        """Get the InvokeAI API version."""
        if not self._http_client:
            raise RuntimeError("Client not connected. Call connect() first.")
            
        try:
            response = await self._http_client.get("/api/v1/app/version")
            if response.status_code == 200:
                data = response.json()
                return data.get("version", "unknown")
            return ""
        except Exception as e:
            print(f"Error getting API version: {e}")
            return ""
    
    async def check_health(self) -> bool:
        """Check if InvokeAI server is healthy and responding."""
        if not self._http_client:
            return False
            
        try:
            response = await self._http_client.get("/api/v1/app/health")
            return response.status_code == 200
        except Exception:
            return False
    
    # Model management
    async def get_models(self, refresh_cache: bool = False) -> List[Model]:
        """
        Get list of available models from InvokeAI.
        
        Args:
            refresh_cache: Force refresh of model cache
            
        Returns:
            List of available models
        """
        if not self._http_client:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        # If not forcing refresh and we have cached models, return them
        if not refresh_cache and self.model_cache_service.has_valid_cache():
            return self.model_cache_service.get_all_models()
        
        try:
            response = await self._http_client.get("/api/v2/models/")
            
            if response.status_code == 200:
                models_data = response.json()
                # Process model data and update cache
                self._build_model_cache(models_data)
                return self.model_cache_service.get_all_models()
            else:
                print(f"Failed to get models: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error getting models: {e}")
            return []
    
    async def find_compatible_vae(self, model_key: str) -> Optional[Model]:
        """Find a compatible VAE for the given model."""
        return self.model_cache_service.get_default_vae_for_model(model_key)
    
    # Graph construction - delegates to GraphBuilder
    def create_generation_graph(self, parameters: GenerationParameters) -> Dict:
        """
        Create a complete graph structure for InvokeAI from user parameters.
        
        Args:
            parameters: User-provided generation parameters
            
        Returns:
            Complete graph structure ready for InvokeAI API
        """
        # Delegate to GraphBuilder class
        return self.graph_builder.build_generation_graph(parameters)
    
    def validate_graph(self, graph: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate that a graph contains all required elements.
        
        Args:
            graph: The graph structure to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for required top-level keys
        if "batch" not in graph:
            return False, "Missing 'batch' key in graph"
            
        batch = graph["batch"]
        if "graph" not in batch:
            return False, "Missing 'graph' key in batch"
            
        graph_def = batch["graph"]
        if "nodes" not in graph_def or "edges" not in graph_def:
            return False, "Missing 'nodes' or 'edges' key in graph definition"
            
        # Check for required node types
        required_node_types = [
            "sdxl_model_loader", "sdxl_compel_prompt", "collect", 
            "noise", "denoise_latents", "vae_loader", 
            "core_metadata", "l2i"
        ]
        
        found_types = set()
        for node_id, node in graph_def["nodes"].items():
            if "type" in node:
                found_types.add(node["type"])
                
        missing_types = set(required_node_types) - found_types
        if missing_types:
            return False, f"Missing required node types: {', '.join(missing_types)}"
            
        # Check data section
        if "data" not in batch or not batch["data"]:
            return False, "Missing 'data' section in batch"
        
        return True, None
    
    # Generation flow
    async def queue_generation(self, parameters: GenerationParameters) -> BatchResponse:
        """
        Queue a generation request with InvokeAI.
        
        Args:
            parameters: Generation parameters
            
        Returns:
            Batch response with batch ID and queue information
        """
        if not self._http_client:
            raise RuntimeError("Client not connected. Call connect() first.")
            
        # Validate parameters
        is_valid, error = parameters.validate()
        if not is_valid:
            raise ValueError(f"Invalid parameters: {error}")
            
        # Create graph using GraphBuilder
        request_data = self.create_generation_graph(parameters)
        
        # Validate graph
        is_valid, error = self.validate_graph(request_data)
        if not is_valid:
            raise ValueError(f"Invalid graph: {error}")
            
        try:
            response = await self._http_client.post(
                "/api/v1/queue/default/enqueue_batch",
                json=request_data,
                timeout=self.timeout
            )
            
            if response.status_code in (200, 201):
                return BatchResponse(**response.json())
            else:
                await self._handle_api_error(response)
        except httpx.HTTPError as e:
            raise ConnectionError(f"HTTP error during generation request: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during generation: {e}")
    
    async def get_batch_status(self, batch_id: str) -> BatchStatus:
        """
        Get status of a batch.
        
        Args:
            batch_id: The ID of the batch to check
            
        Returns:
            Current status of the batch
        """
        if not self._http_client:
            raise RuntimeError("Client not connected. Call connect() first.")
            
        try:
            response = await self._http_client.get(
                f"/api/v1/queue/default/b/{batch_id}/status"
            )
            
            if response.status_code == 200:
                return BatchStatus(**response.json())
            else:
                await self._handle_api_error(response)
        except Exception as e:
            raise RuntimeError(f"Error checking batch status: {e}")
    
    async def wait_for_batch_completion(self, batch_id: str, timeout_seconds: int = 300) -> BatchResult:
        """
        Wait for a batch to complete with exponential backoff polling.
        
        Args:
            batch_id: The ID of the batch to wait for
            timeout_seconds: Maximum time to wait (seconds)
            
        Returns:
            Information about the completed batch including image names
        """
        start_time = time.time()
        wait_time = 2  # Initial wait in seconds
        
        # Initial wait
        await asyncio.sleep(2)
        
        while time.time() - start_time < timeout_seconds:
            status = await self.get_batch_status(batch_id)
            
            if status.is_complete():
                # Batch processing is done
                image_names = status.get_completed_image_names()
                return BatchResult(
                    batch_id=batch_id,
                    image_names=image_names,
                    is_success=len(image_names) > 0,
                    error=None
                )
            elif status.is_failed():
                # Batch failed
                return BatchResult(
                    batch_id=batch_id,
                    image_names=[],
                    is_success=False,
                    error="Batch processing failed"
                )
                
            # Calculate progress for UI feedback
            progress = status.calculate_progress()
            print(f"Batch progress: {progress}%")
            
            # Adjust wait time with exponential backoff (max 10 seconds)
            wait_time = min(wait_time * 1.5, 10)
            await asyncio.sleep(wait_time)
        
        # Timeout reached
        return BatchResult(
            batch_id=batch_id,
            image_names=[],
            is_success=False,
            error=f"Timeout after {timeout_seconds} seconds"
        )
    
    # Image retrieval
    async def list_recent_images(self, limit: int, since: Optional[datetime] = None) -> List[ImageInfo]:
        """
        List recently generated images.
        
        Args:
            limit: Maximum number of images to return
            since: Optional timestamp to filter by
            
        Returns:
            List of recent image information
        """
        if not self._http_client:
            raise RuntimeError("Client not connected. Call connect() first.")
            
        params = {"limit": limit}
        if since:
            params["since"] = since.isoformat()
            
        try:
            response = await self._http_client.get("/api/v1/images/", params=params)
            
            if response.status_code == 200:
                data = response.json()
                image_infos = []
                
                for item in data.get("items", []):
                    image_infos.append(ImageInfo(
                        name=item["image_name"],
                        width=item["width"],
                        height=item["height"],
                        created_at=datetime.fromisoformat(item["created_at"].replace(' ', 'T')),
                        has_metadata=True
                    ))
                    
                return image_infos
            else:
                await self._handle_api_error(response)
                return []
        except Exception as e:
            print(f"Error listing images: {e}")
            return []
    
    async def get_image(self, image_name: str) -> bytes:
        """Get full-resolution image data."""
        if not self._http_client:
            raise RuntimeError("Client not connected. Call connect() first.")
            
        try:
            response = await self._http_client.get(
                f"/api/v1/images/i/{image_name}/full",
                timeout=httpx.Timeout(connect=self.timeout.connect, read=60.0)  # Longer timeout for images
            )
            
            if response.status_code == 200:
                return response.content
            else:
                await self._handle_api_error(response)
                return b""
        except Exception as e:
            print(f"Error getting image: {e}")
            return b""
    
    async def get_thumbnail(self, image_name: str) -> bytes:
        """Get thumbnail image data."""
        if not self._http_client:
            raise RuntimeError("Client not connected. Call connect() first.")
            
        try:
            response = await self._http_client.get(
                f"/api/v1/images/i/{image_name}/thumbnail"
            )
            
            if response.status_code == 200:
                return response.content
            else:
                await self._handle_api_error(response)
                return b""
        except Exception as e:
            print(f"Error getting thumbnail: {e}")
            return b""
    
    async def get_image_metadata(self, image_name: str) -> Dict:
        """Get metadata for a specific image."""
        if not self._http_client:
            raise RuntimeError("Client not connected. Call connect() first.")
            
        try:
            response = await self._http_client.get(
                f"/api/v1/images/i/{image_name}/metadata"
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                await self._handle_api_error(response)
                return {}
        except Exception as e:
            print(f"Error getting metadata: {e}")
            return {}
    
    # Clean-up operations
    async def delete_image(self, image_name: str) -> bool:
        """Delete an image from InvokeAI."""
        if not self._http_client:
            raise RuntimeError("Client not connected. Call connect() first.")
            
        try:
            response = await self._http_client.delete(
                f"/api/v1/images/i/{image_name}"
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"Error deleting image: {e}")
            return False
    
    # Cache and helper methods
    def _build_model_cache(self, models_data: Dict) -> None:
        """Process model data and update model cache."""
        models = models_data.get("models", [])
        
        # Process and categorize models
        main_models = []
        vae_models = []
        
        for model in models:
            if model.get("type") == "main":
                main_models.append(model)
            elif model.get("type") == "vae":
                vae_models.append(model)
        
        # Update model cache service
        self.model_cache_service.update_models(main_models, vae_models)
        
        # Map compatible VAEs to main models
        for main_model in main_models:
            base = main_model.get("base")
            for vae in vae_models:
                if vae.get("base") == base:
                    # This VAE is compatible with this model
                    self.model_cache_service.add_compatible_vae(
                        main_model.get("key"),
                        vae.get("key"),
                        is_default="fp16" in vae.get("name", "").lower()  # Heuristic for default VAE
                    )
    
    # No need for _create_unique_node_id - GraphBuilder handles this
    
    async def _handle_api_error(self, response):
        """Handle error responses from the API."""
        try:
            error_data = response.json()
            error_msg = error_data.get("detail", f"API error: {response.status_code}")
            
            # Map error types
            if "CUDA out of memory" in error_msg:
                raise ResourceError("GPU memory insufficient for this request")
            elif "Model with key" in error_msg and "not found" in error_msg:
                raise ModelError("Model not found or hash mismatch")
            else:
                raise APIError(error_msg)
        except (json.JSONDecodeError, KeyError):
            # Couldn't parse error JSON
            raise APIError(f"API error {response.status_code}: {response.text}")
            
    async def close(self):
        """Close the client and any open connections."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
```

```python
class GenerationParameters:
    """Simple parameters for image generation that will be translated to graph structure."""
    
    def __init__(
        self,
        prompt: str,
        model_key: str,
        negative_prompt: Optional[str] = None,
        vae_key: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        steps: int = 30,
        cfg_scale: float = 7.5,
        scheduler: str = "euler",
        batch_size: int = 1,
        seed: Optional[int] = None,
        correlation_id: Optional[str] = None
    ):
        self.prompt = prompt
        self.model_key = model_key
        self.negative_prompt = negative_prompt
        self.vae_key = vae_key
        self.width = width
        self.height = height
        self.steps = steps
        self.cfg_scale = cfg_scale
        self.scheduler = scheduler
        self.batch_size = min(batch_size, 10)  # Cap at 10 for safety
        self.seed = seed
        self.correlation_id = correlation_id or str(uuid.uuid4())
        
    def validate(self) -> Tuple[bool, Optional[str]]:
        """Validate parameters for common issues."""
        if not self.prompt:
            return False, "Prompt cannot be empty"
            
        if not self.model_key:
            return False, "Model key must be provided"
            
        if self.width * self.height > 1920 * 1088:
            return False, "Image dimensions too large"
            
        if self.steps > 50:
            return False, "Steps value too high"
            
        if self.cfg_scale < 1.0:
            return False, "CFG Scale must be at least 1.0"
            
        return True, None
```

```python
# Construct InvokeAI Generation Graph from User Input Parameters
class GraphBuilder:
    """Helper class for constructing InvokeAI graph structures from simple user parameters."""
    
    def __init__(self, model_cache_service):
        """Initialize with access to model information."""
        self.model_cache = model_cache_service
        self.node_id_counter = {}
    
    def create_unique_node_id(self, prefix: str) -> str:
        """Generate a unique ID for a node with given prefix."""
        if prefix not in self.node_id_counter:
            self.node_id_counter[prefix] = 0
        self.node_id_counter[prefix] += 1
        return f"{prefix}:{self.node_id_counter[prefix]}"
    
    def build_generation_graph(self, params: GenerationParameters) -> Dict:
        """
        Constructs a complete InvokeAI graph from simplified user parameters.
        
        Args:
            params: User-provided generation parameters
            
        Returns:
            Complete graph structure ready for InvokeAI API
        """
        # Create node IDs for all required nodes
        nodes = {
            "model_loader": self.create_unique_node_id("sdxl_model_loader"),
            "pos_prompt": self.create_unique_node_id("sdxl_compel_prompt"),
            "neg_prompt": self.create_unique_node_id("sdxl_compel_prompt"),
            "pos_collect": self.create_unique_node_id("collect"),
            "neg_collect": self.create_unique_node_id("collect"),
            "noise": self.create_unique_node_id("noise"),
            "denoise": self.create_unique_node_id("denoise_latents"),
            "vae_loader": self.create_unique_node_id("vae_loader"),
            "metadata": self.create_unique_node_id("core_metadata"),
            "output": self.create_unique_node_id("l2i")
        }
        
        # Get model and VAE details from cache
        model_info = self.model_cache.get_model_by_key(params.model_key)
        if not model_info:
            raise ValueError(f"Model with key {params.model_key} not found in cache")
            
        vae_info = None
        if params.vae_key:
            vae_info = self.model_cache.get_model_by_key(params.vae_key)
        else:
            # Find default VAE for this model
            vae_info = self.model_cache.get_default_vae_for_model(params.model_key)
            
        if not vae_info:
            raise ValueError(f"No compatible VAE found for model {params.model_key}")
        
        # Construct graph structure
        graph = {
            "id": f"sdxl_graph:{uuid.uuid4().hex[:8]}",
            "nodes": self._build_nodes(nodes, params, model_info, vae_info),
            "edges": self._build_edges(nodes)
        }
        
        # Construct data overrides section
        data = self._build_data_section(nodes, params)
        
        return {
            "prepend": False,
            "batch": {
                "graph": graph,
                "runs": 1,
                "data": data,
                "origin": "photo_gallery",
                "destination": "gallery"
            }
        }
    
    def _build_nodes(self, nodes, params, model_info, vae_info) -> Dict:
        """Construct all node definitions for the graph."""
        return {
            # Model loader node
            nodes["model_loader"]: {
                "type": "sdxl_model_loader",
                "id": nodes["model_loader"],
                "model": {
                    "key": model_info["key"],
                    "name": model_info["name"],
                    "base": model_info["base"],
                    "type": "main",
                    "hash": model_info["hash"]
                },
                "is_intermediate": True,
                "use_cache": True
            },
            
            # Positive prompt node
            nodes["pos_prompt"]: {
                "type": "sdxl_compel_prompt",
                "id": nodes["pos_prompt"],
                "prompt": params.prompt,
                "style": params.prompt,  # Style and prompt are same by default
                "is_intermediate": True,
                "use_cache": True
            },
            
            # Positive collect node
            nodes["pos_collect"]: {
                "type": "collect",
                "id": nodes["pos_collect"],
                "is_intermediate": True,
                "use_cache": True
            },
            
            # Negative prompt node
            nodes["neg_prompt"]: {
                "type": "sdxl_compel_prompt",
                "id": nodes["neg_prompt"],
                "prompt": params.negative_prompt or "",
                "style": "",  # Style is usually empty for negative prompts
                "is_intermediate": True,
                "use_cache": True
            },
            
            # Negative collect node
            nodes["neg_collect"]: {
                "type": "collect",
                "id": nodes["neg_collect"],
                "is_intermediate": True,
                "use_cache": True
            },
            
            # Noise generator node
            nodes["noise"]: {
                "type": "noise",
                "id": nodes["noise"],
                "seed": params.seed if params.seed is not None else random.randint(1, 1000000),
                "width": params.width,
                "height": params.height,
                "use_cpu": True,  # More reliable even with GPU
                "is_intermediate": True,
                "use_cache": True
            },
            
            # Denoiser node
            nodes["denoise"]: {
                "type": "denoise_latents",
                "id": nodes["denoise"],
                "cfg_scale": params.cfg_scale,
                "cfg_rescale_multiplier": 0,  # Default value
                "scheduler": params.scheduler,
                "steps": params.steps,
                "denoising_start": 0,
                "denoising_end": 1,
                "is_intermediate": True,
                "use_cache": True
            },
            
            # VAE loader node
            nodes["vae_loader"]: {
                "type": "vae_loader",
                "id": nodes["vae_loader"],
                "vae_model": {
                    "key": vae_info["key"],
                    "hash": vae_info["hash"],
                    "name": vae_info["name"],
                    "base": vae_info["base"],
                    "type": "vae"
                },
                "is_intermediate": True,
                "use_cache": True
            },
            
            # Metadata node - critical for storing generation parameters
            nodes["metadata"]: {
                "id": nodes["metadata"],
                "type": "core_metadata",
                "is_intermediate": True,
                "use_cache": True,
                "generation_mode": "sdxl_txt2img",
                "cfg_scale": params.cfg_scale,
                "cfg_rescale_multiplier": 0,
                "width": params.width,
                "height": params.height,
                "negative_prompt": params.negative_prompt or "",
                "model": {
                    "key": model_info["key"],
                    "name": model_info["name"],
                    "base": model_info["base"],
                    "type": "main",
                    "hash": model_info["hash"]
                },
                "steps": params.steps,
                "rand_device": "cpu",
                "scheduler": params.scheduler,
                "vae": {
                    "key": vae_info["key"],
                    "hash": vae_info["hash"],
                    "name": vae_info["name"],
                    "base": vae_info["base"],
                    "type": "vae"
                }
            },
            
            # Output node
            nodes["output"]: {
                "type": "l2i",
                "id": nodes["output"],
                "fp32": False,
                "is_intermediate": False,
                "use_cache": False
            }
        }
    
    def _build_edges(self, nodes) -> List[Dict]:
        """Construct all edges connecting the nodes."""
        return [
            # Model connections
            {"source": {"node_id": nodes["model_loader"], "field": "unet"},
             "destination": {"node_id": nodes["denoise"], "field": "unet"}},
            {"source": {"node_id": nodes["model_loader"], "field": "clip"},
             "destination": {"node_id": nodes["pos_prompt"], "field": "clip"}},
            {"source": {"node_id": nodes["model_loader"], "field": "clip"},
             "destination": {"node_id": nodes["neg_prompt"], "field": "clip"}},
            {"source": {"node_id": nodes["model_loader"], "field": "clip2"},
             "destination": {"node_id": nodes["pos_prompt"], "field": "clip2"}},
            {"source": {"node_id": nodes["model_loader"], "field": "clip2"},
             "destination": {"node_id": nodes["neg_prompt"], "field": "clip2"}},
            
            # Prompt conditioning connections
            {"source": {"node_id": nodes["pos_prompt"], "field": "conditioning"},
             "destination": {"node_id": nodes["pos_collect"], "field": "item"}},
            {"source": {"node_id": nodes["neg_prompt"], "field": "conditioning"},
             "destination": {"node_id": nodes["neg_collect"], "field": "item"}},
            
            # Conditioning to denoiser
            {"source": {"node_id": nodes["pos_collect"], "field": "collection"},
             "destination": {"node_id": nodes["denoise"], "field": "positive_conditioning"}},
            {"source": {"node_id": nodes["neg_collect"], "field": "collection"},
             "destination": {"node_id": nodes["denoise"], "field": "negative_conditioning"}},
            
            # Noise to denoiser
            {"source": {"node_id": nodes["noise"], "field": "noise"},
             "destination": {"node_id": nodes["denoise"], "field": "noise"}},
            
            # Denoiser to output
            {"source": {"node_id": nodes["denoise"], "field": "latents"},
             "destination": {"node_id": nodes["output"], "field": "latents"}},
            
            # VAE to output
            {"source": {"node_id": nodes["vae_loader"], "field": "vae"},
             "destination": {"node_id": nodes["output"], "field": "vae"}},
            
            # Metadata to output
            {"source": {"node_id": nodes["metadata"], "field": "metadata"},
             "destination": {"node_id": nodes["output"], "field": "metadata"}}
        ]
    
    def _build_data_section(self, nodes, params) -> List[List[Dict]]:
        """
        Build the data section with parameter overrides.
        This is critical for batch processing and metadata preservation.
        """
        # Generate seeds if needed
        if params.batch_size > 1:
            if params.seed is not None:
                # Deterministic seeds based on starting seed
                seeds = [params.seed + i for i in range(params.batch_size)]
            else:
                # Random seeds
                seeds = [random.randint(1, 1000000) for _ in range(params.batch_size)]
        else:
            seeds = [params.seed if params.seed is not None else random.randint(1, 1000000)]
        
        # Construct data overrides
        data_items = [
            # Seed overrides - must be set in both noise and metadata nodes
            {"node_path": nodes["noise"], "field_name": "seed", "items": seeds},
            {"node_path": nodes["metadata"], "field_name": "seed", "items": seeds},
            
            # Critical: Prompt overrides for metadata preservation
            {"node_path": nodes["metadata"], "field_name": "positive_prompt", "items": [params.prompt]},
            {"node_path": nodes["metadata"], "field_name": "positive_style_prompt", "items": [params.prompt]}
        ]
        
        # Add correlation ID if provided
        if params.correlation_id:
            # Embed correlation ID in prompts for verification during retrieval
            modified_prompt = f"{params.prompt} [CID:{params.correlation_id}]"
            data_items.extend([
                {"node_path": nodes["pos_prompt"], "field_name": "prompt", "items": [modified_prompt]},
                {"node_path": nodes["metadata"], "field_name": "positive_prompt", "items": [modified_prompt]}
            ])
        
        return [data_items]
```

```python
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
```

```python 
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
```
```python
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
```
```python
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