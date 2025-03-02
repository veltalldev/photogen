# Photo Gallery Implementation Guide

This guide provides practical implementation guidance for the Photo Gallery application based on the simplified architecture. It focuses on concrete patterns, examples, and best practices to ensure a consistent and maintainable codebase.

## 1. Core Implementation Patterns

### 1.1 Synchronous Database Operations

Use direct, synchronous SQLAlchemy operations for database interactions to keep the code simple and readable:

```python
# Example repository method
def get_photo_by_id(self, photo_id: UUID) -> Optional[Photo]:
    """Get a photo by ID."""
    return self.db_session.query(Photo).filter(Photo.id == photo_id).first()

def update_photo(self, photo_id: UUID, data: Dict) -> Optional[Photo]:
    """Update a photo with the provided data."""
    photo = self.get_photo_by_id(photo_id)
    if not photo:
        return None
        
    # Update photo fields
    for key, value in data.items():
        if hasattr(photo, key):
            setattr(photo, key, value)
    
    # Commit changes
    self.db_session.commit()
    return photo
```

### 1.2 Direct Retrieval Tracking

Track image retrieval status directly in the photos table to simplify the retrieval workflow:

```python
def mark_retrieval_started(self, photo_id: UUID, invoke_id: str) -> bool:
    """Mark photo retrieval as started."""
    photo = self.get_photo_by_id(photo_id)
    if not photo:
        return False
        
    photo.invoke_id = invoke_id
    photo.retrieval_status = 'pending'
    photo.retrieval_attempts = 0
    self.db_session.commit()
    return True

def mark_retrieval_complete(self, photo_id: UUID, local_path: str, thumbnail_path: str) -> bool:
    """Mark photo retrieval as complete."""
    photo = self.get_photo_by_id(photo_id)
    if not photo:
        return False
        
    photo.retrieval_status = 'completed'
    photo.local_storage_path = local_path
    photo.local_thumbnail_path = thumbnail_path
    self.db_session.commit()
    return True

def mark_retrieval_failed(self, photo_id: UUID, error_message: str) -> bool:
    """Mark photo retrieval as failed."""
    photo = self.get_photo_by_id(photo_id)
    if not photo:
        return False
        
    photo.retrieval_attempts += 1
    photo.retrieval_status = 'failed'
    photo.retrieval_error = error_message
    photo.last_retrieval_attempt = datetime.now()
    self.db_session.commit()
    return True
```

### 1.3 Exception Handling

Create specific exception classes and use a consistent pattern for error handling:

```python
# Exception classes
class PhotoGalleryError(Exception):
    """Base class for application errors."""
    pass

class ResourceNotFoundError(PhotoGalleryError):
    """Raised when a requested resource is not found."""
    pass

class ValidationError(PhotoGalleryError):
    """Raised when input validation fails."""
    pass

class InvokeAIError(PhotoGalleryError):
    """Base class for InvokeAI-related errors."""
    pass

class ConnectionError(InvokeAIError):
    """Raised when connection to InvokeAI fails."""
    pass

# Usage in service methods
def get_photo(self, photo_id: UUID) -> Photo:
    """Get a photo by ID."""
    photo = self.photo_repository.get_photo_by_id(photo_id)
    if not photo:
        raise ResourceNotFoundError(f"Photo with ID {photo_id} not found")
    return photo

# Error response mapping in API layer
@router.get("/photos/{photo_id}")
def get_photo(photo_id: UUID, photo_service: PhotoService = Depends(get_photo_service)):
    try:
        photo = photo_service.get_photo(photo_id)
        return photo
    except ResourceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Photo {photo_id} not found")
    except Exception as e:
        # Log exception
        logger.exception(f"Error retrieving photo {photo_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### 1.4 Consistent File Paths

Use a consistent pattern for generating file paths to maintain a clear organization:

```python
def generate_paths(self, photo: Photo) -> Dict[str, str]:
    """Generate file paths for a photo."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    if photo.is_generated:
        # Extract session and step information from related entities
        step = photo.step_alternative.step if hasattr(photo, 'step_alternative') else None
        session_id = step.session_id if step else 'unknown'
        step_id = step.id if step else 'unknown'
        
        # Session-based paths for active workflow
        session_path = f"data/photos/generated/sessions/{session_id}/{step_id}"
        session_sub_path = "selected" if step and step.selected_image_id == photo.id else "variants"
        
        # Image paths
        image_path = f"{session_path}/{session_sub_path}/{photo.id}.png"
        thumbnail_path = f"data/photos/thumbnails/generated/sessions/{session_id}/{step_id}/{session_sub_path}/{photo.id}.webp"
        
        # Add completed paths for selected images
        if step and step.selected_image_id == photo.id:
            completed_path = f"data/photos/generated/completed/{today}/{photo.id}.png"
            completed_thumbnail_path = f"data/photos/thumbnails/generated/completed/{today}/{photo.id}.webp"
            
            return {
                "image_path": image_path,
                "thumbnail_path": thumbnail_path,
                "completed_path": completed_path,
                "completed_thumbnail_path": completed_thumbnail_path
            }
        
        return {
            "image_path": image_path,
            "thumbnail_path": thumbnail_path
        }
    else:
        # Uploaded photo paths
        ext = os.path.splitext(photo.filename)[1].lower()
        image_path = f"data/photos/uploaded/{today}/{photo.id}{ext}"
        thumbnail_path = f"data/photos/thumbnails/uploaded/{today}/{photo.id}.webp"
        
        return {
            "image_path": image_path,
            "thumbnail_path": thumbnail_path
        }
```

## 2. Key Components Implementation

### 2.1 Database Models

Implement clear, focused SQLAlchemy models with appropriate relationships:

```python
# Base model with common functionality
class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        # Convert CamelCase to snake_case
        return re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

# Photo model
class Photo(Base):
    # Basic metadata
    filename: Mapped[str] = mapped_column(String, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    
    # Generation metadata
    is_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    generation_prompt: Mapped[Optional[str]] = mapped_column(Text)
    generation_negative_prompt: Mapped[Optional[str]] = mapped_column(Text)
    generation_params: Mapped[Optional[Dict]] = mapped_column(JSONB)
    source_image_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("photo.id"))
    
    # InvokeAI specific fields
    invoke_id: Mapped[Optional[str]] = mapped_column(String)
    model_key: Mapped[Optional[str]] = mapped_column(String)
    model_hash: Mapped[Optional[str]] = mapped_column(String)
    model_name: Mapped[Optional[str]] = mapped_column(String)
    
    # Retrieval tracking
    retrieval_status: Mapped[str] = mapped_column(String, default="completed")
    retrieval_attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_retrieval_attempt: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    retrieval_error: Mapped[Optional[str]] = mapped_column(Text)
    
    # File paths
    local_storage_path: Mapped[Optional[str]] = mapped_column(String)
    local_thumbnail_path: Mapped[Optional[str]] = mapped_column(String)
    
    # System metadata
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    source_image: Mapped[Optional["Photo"]] = relationship(
        "Photo", remote_side=[id], back_populates="derived_images"
    )
    derived_images: Mapped[List["Photo"]] = relationship(
        "Photo", back_populates="source_image", uselist=True, remote_side=[source_image_id]
    )
    albums: Mapped[List["Album"]] = relationship(
        "Album", secondary="album_photo", back_populates="photos"
    )
    step_alternatives: Mapped[List["StepAlternative"]] = relationship(
        "StepAlternative", back_populates="photo"
    )
    
    # Methods
    def to_dict(self) -> Dict:
        """Convert photo to dictionary."""
        return {
            "id": str(self.id),
            "filename": self.filename,
            "width": self.width,
            "height": self.height,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_generated": self.is_generated,
            "generation_prompt": self.generation_prompt,
            "retrieval_status": self.retrieval_status,
            "thumbnail_url": f"/api/photos/{self.id}/thumbnail" if self.local_thumbnail_path else None,
            "url": f"/api/photos/{self.id}" if self.local_storage_path else None
        }
```

### 2.2 API Routes

Implement clean, focused API routes with consistent error handling:

```python
# Photo routes
router = APIRouter(prefix="/photos", tags=["photos"])

@router.get("/")
def list_photos(
    limit: int = 50,
    offset: int = 0,
    generated: Optional[bool] = None,
    album_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """List photos with optional filtering."""
    photo_service = PhotoService(db)
    
    filters = {
        "limit": limit,
        "offset": offset
    }
    
    if generated is not None:
        filters["generated"] = generated
    
    if album_id:
        filters["album_id"] = album_id
    
    result = photo_service.list_photos(filters)
    
    return {
        "items": [photo.to_dict() for photo in result["items"]],
        "total": result["total"],
        "limit": limit,
        "offset": offset
    }

@router.get("/{id}")
def get_photo(id: UUID, db: Session = Depends(get_db)):
    """Get a specific photo."""
    photo_service = PhotoService(db)
    photo = photo_service.get_photo(id)
    
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    # If photo exists but file doesn't, attempt to retrieve it for generated images
    if photo.is_generated and photo.retrieval_status != "completed":
        photo_service.retry_retrieval(id)
        raise HTTPException(
            status_code=202,
            detail=f"Photo retrieval in progress. Current status: {photo.retrieval_status}"
        )
    
    if not photo.local_storage_path or not os.path.exists(photo.local_storage_path):
        raise HTTPException(status_code=404, detail="Photo file not found")
    
    return FileResponse(
        photo.local_storage_path,
        media_type=photo.mime_type,
        filename=photo.filename
    )
```

### 2.3 InvokeAI Client

Implement a robust client for InvokeAI interaction:

```python
class InvokeAIClient:
    """Client for interacting with InvokeAI API."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """Initialize the InvokeAI client."""
        self.base_url = base_url
        self.timeout = timeout
        self.connected = False
        self.api_version = None
    
    def connect(self) -> bool:
        """Connect to InvokeAI API and verify availability."""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/app/version", 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.connected = True
                self.api_version = response.json().get("version")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def get_models(self) -> List[Dict]:
        """Get list of available models from InvokeAI."""
        if not self.connected and not self.connect():
            raise ConnectionError("Not connected to InvokeAI")
            
        try:
            response = requests.get(
                f"{self.base_url}/api/v2/models/", 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json().get("models", [])
            
            logger.error(f"Failed to get models: {response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Error getting models: {e}")
            raise ConnectionError(f"Error retrieving models: {e}")
    
    def queue_generation(self, params: Dict) -> Dict:
        """Queue a generation request with InvokeAI."""
        if not self.connected and not self.connect():
            raise ConnectionError("Not connected to InvokeAI")
        
        graph_data = self._build_generation_graph(params)
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/queue/default/enqueue_batch",
                json=graph_data,
                timeout=self.timeout
            )
            
            if response.status_code in (200, 201):
                return response.json()
            else:
                error_msg = self._parse_error_response(response)
                raise GenerationError(f"Generation request failed: {error_msg}")
        except Exception as e:
            if isinstance(e, GenerationError):
                raise
            logger.error(f"Error queueing generation: {e}")
            raise GenerationError(f"Error queueing generation: {e}")
```

### 2.4 Background Tasks

Implement a simple background task scheduler for recurring operations:

```python
class BackgroundTaskManager:
    """Manages background tasks for the application."""
    
    def __init__(self):
        """Initialize the background task manager."""
        self.scheduler = None
        self.tasks = []
    
    def schedule_task(self, name: str, interval: int, func: Callable, *args, **kwargs):
        """Schedule a task to run at regular intervals."""
        task = {
            "name": name,
            "interval": interval,
            "func": func,
            "args": args,
            "kwargs": kwargs,
            "last_run": None
        }
        
        self.tasks.append(task)
        
        # Add to scheduler
        if interval < 60:
            # Schedule in seconds
            schedule.every(interval).seconds.do(
                self._run_task, task=task
            )
        else:
            # Schedule in minutes
            schedule.every(interval // 60).minutes.do(
                self._run_task, task=task
            )
    
    def _run_task(self, task):
        """Run a scheduled task."""
        try:
            result = task["func"](*task["args"], **task["kwargs"])
            task["last_run"] = datetime.now()
            task["last_result"] = "success"
            return result
        except Exception as e:
            logger.exception(f"Error running task {task['name']}: {e}")
            task["last_run"] = datetime.now()
            task["last_result"] = str(e)
    
    def start(self):
        """Start the background task scheduler."""
        def scheduler_thread():
            while True:
                schedule.run_pending()
                time.sleep(1)
        
        self.scheduler = threading.Thread(target=scheduler_thread, daemon=True)
        self.scheduler.start()
    
    def stop(self):
        """Stop the background task scheduler."""
        # Nothing to do since we're using a daemon thread
        pass
```

## 3. Key Workflows Implementation

### 3.1 Photo Upload Workflow

```python
def upload_photo(self, file_data: bytes, filename: str) -> Photo:
    """Process and store an uploaded photo."""
    try:
        # Validate file
        content_type, width, height = self._validate_image(file_data)
        
        # Create photo record
        photo = Photo(
            filename=filename,
            width=width,
            height=height,
            file_size=len(file_data),
            mime_type=content_type,
            is_generated=False
        )
        
        self.db_session.add(photo)
        self.db_session.commit()
        
        # Generate paths
        paths = self.file_service.generate_paths(photo)
        
        # Save file
        self.file_service.save_file(paths["image_path"], file_data)
        
        # Create and save thumbnail
        thumbnail_data = self.file_service.create_thumbnail(file_data)
        self.file_service.save_file(paths["thumbnail_path"], thumbnail_data)
        
        # Update photo with paths
        photo.local_storage_path = paths["image_path"]
        photo.local_thumbnail_path = paths["thumbnail_path"]
        self.db_session.commit()
        
        return photo
        
    except ValidationError as e:
        raise e
    except Exception as e:
        logger.exception(f"Error uploading photo: {e}")
        raise PhotoProcessingError(f"Error processing photo: {e}")
```

### 3.2 Image Generation Workflow

```python
def create_step(self, session_id: UUID, params: Dict) -> Tuple[GenerationStep, Dict]:
    """Create and execute a generation step."""
    # Get session
    session = self.db_session.query(GenerationSession).get(session_id)
    if not session:
        raise ResourceNotFoundError(f"Session with ID {session_id} not found")
    
    # Validate parameters
    if "prompt" not in params or not params["prompt"]:
        raise ValidationError("Prompt is required")
    
    if "model_key" not in params or not params["model_key"]:
        raise ValidationError("Model key is required")
    
    if "model_hash" not in params or not params["model_hash"]:
        raise ValidationError("Model hash is required")
    
    # Get position for this step
    position = self._get_next_step_position(session_id)
    
    # Create correlation ID
    correlation_id = params.get("correlation_id", str(uuid.uuid4()))
    
    # Create step record
    step = GenerationStep(
        session_id=session_id,
        parent_id=params.get("parent_id"),
        prompt=params["prompt"],
        negative_prompt=params.get("negative_prompt", ""),
        parameters=params.get("parameters", {}),
        model_key=params["model_key"],
        model_hash=params["model_hash"],
        model_name=params.get("model_name", ""),
        correlation_id=correlation_id,
        position=position,
        status="pending",
        batch_size=params.get("batch_size", 1)
    )
    
    self.db_session.add(step)
    self.db_session.commit()
    
    # Prepare generation parameters
    generation_params = {
        "prompt": step.prompt,
        "negative_prompt": step.negative_prompt,
        "model_key": step.model_key,
        "model_hash": step.model_hash,
        "batch_size": step.batch_size,
        "correlation_id": step.correlation_id,
        # Include other parameters from params
        **params.get("parameters", {})
    }
    
    # Submit generation request
    try:
        response = self.invokeai_client.queue_generation(generation_params)
        
        # Update step with batch ID
        step.batch_id = response["batch_id"]
        step.status = "processing"
        self.db_session.commit()
        
        # Start background monitoring
        self._schedule_batch_status_check(step.id)
        
        return step, response
    except Exception as e:
        # Update step with error
        step.status = "failed"
        step.error_message = str(e)
        self.db_session.commit()
        
        logger.exception(f"Error creating generation step: {e}")
        
        return step, {"error": str(e)}

def _schedule_batch_status_check(self, step_id: UUID):
    """Schedule a background task to check batch status."""
    threading.Thread(
        target=self._monitor_batch_status,
        args=(step_id,),
        daemon=True
    ).start()

def _monitor_batch_status(self, step_id: UUID):
    """Monitor batch status and process results when complete."""
    try:
        # Get step
        step = self.db_session.query(GenerationStep).get(step_id)
        if not step or not step.batch_id:
            logger.error(f"Invalid step ID or missing batch ID: {step_id}")
            return
        
        # Wait for batch completion
        status = self.invokeai_client.wait_for_batch_completion(step.batch_id)
        
        # Process completed batch
        if status["is_complete"]:
            self._process_completed_batch(step, status)
    except Exception as e:
        logger.exception(f"Error monitoring batch status: {e}")
        
        # Update step with error
        try:
            step = self.db_session.query(GenerationStep).get(step_id)
            if step:
                step.status = "failed"
                step.error_message = str(e)
                self.db_session.commit()
        except Exception:
            pass

def _process_completed_batch(self, step: GenerationStep, status: Dict):
    """Process a completed generation batch."""
    # Update step status
    step.status = "completed"
    step.completed_at = datetime.now()
    self.db_session.commit()
    
    # Get image names from batch status
    image_names = status.get("image_names", [])
    
    if not image_names:
        # Try alternative approach to get image names
        image_names = self._get_recent_images(step.batch_size)
    
    # Create photo records for each image
    for image_name in image_names:
        self._create_photo_for_generated_image(step, image_name)
        
def _get_recent_images(self, count: int) -> List[str]:
    """Get the most recent images from InvokeAI."""
    try:
        # Query for recent images
        images = self.invokeai_client.list_recent_images(limit=count)
        return [img["image_name"] for img in images]
    except Exception as e:
        logger.error(f"Error getting recent images: {e}")
        return []
```

## 4. Implementation Limitations and Workarounds

### 4.1 InvokeAI Image Correlation Limitation

**Important Limitation:** The InvokeAI API does not provide a direct way to get the invoke_IDs of newly generated images from a batch request. This creates a challenge in correlating batch requests with their resulting images.

**Workaround Strategy:**

1. **Recent Images Approach:**
   - After batch completion, query for the most recent images sorted by creation time (default ordering)
   - Limit the number to the exact size of the batch we requested
   - If all goes well, the returned images should exactly match our newly generated ones

2. **Potential Issues:**
   - If generation encounters problems, some requested images might not be successfully generated
   - This can result in older images being included in the results
   - You might end up with duplicate references to the same images (same invoke_IDs but different internal UUIDs)

3. **Mitigation Options:**
   - Use correlation IDs embedded in prompts to verify images belong to the current batch
   - Implement logic to check for and handle duplicate invoke_IDs
   - Develop a periodic garbage collector to clean up duplicate references
   - Consider implementing a verification step that checks metadata for expected properties

**Example Implementation:**

```python
def correlate_batch_with_images(self, batch_id: str, batch_size: int, correlation_id: Optional[str] = None) -> List[str]:
    """Correlate a batch with its generated images."""
    # First try to get image names from batch status
    status = self.invokeai_client.get_batch_status(batch_id)
    image_names = []
    
    for item in status.get("items", []):
        if item.get("status") == "completed" and "result" in item:
            image_names.append(item["result"].get("image_name"))
    
    # If we have the expected number of images, return them
    if len(image_names) == batch_size:
        return image_names
    
    # Otherwise, try the recent images approach
    recent_images = self.invokeai_client.list_recent_images(limit=batch_size * 2)  # Get more than needed for verification
    
    # If we have a correlation ID, filter by it
    if correlation_id:
        verified_images = []
        
        for img in recent_images:
            # Check image metadata for correlation ID
            metadata = self.invokeai_client.get_image_metadata(img["image_name"])
            prompt = metadata.get("metadata", {}).get("positive_prompt", "")
            
            # If prompt contains our correlation marker, it's one of ours
            if f"[CID:{correlation_id}]" in prompt:
                verified_images.append(img["image_name"])
                
                # If we've found enough, stop looking
                if len(verified_images) == batch_size:
                    break
        
        if verified_images:
            return verified_images
    
    # If all else fails, just return the most recent images
    return [img["image_name"] for img in recent_images[:batch_size]]
```

### 4.2 Other Implementation Considerations

#### 4.2.1 File Path Management

Implement a robust file path generation strategy that ensures consistent organization:

```python
def generate_file_paths(self, photo, is_selected=False):
    """Generate file paths for a photo."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    if photo.is_generated:
        step = self._get_step_for_photo(photo.id)
        session_id = step.session_id if step else "unknown"
        step_id = step.id if step else "unknown"
        
        # Create directory structure if needed
        base_dir = f"data/photos/generated/sessions/{session_id}/{step_id}"
        variant_type = "selected" if is_selected else "variants"
        os.makedirs(f"{base_dir}/{variant_type}", exist_ok=True)
        os.makedirs(f"data/photos/thumbnails/generated/sessions/{session_id}/{step_id}/{variant_type}", exist_ok=True)
        
        # Create paths
        paths = {
            "image_path": f"{base_dir}/{variant_type}/{photo.id}.png",
            "thumbnail_path": f"data/photos/thumbnails/generated/sessions/{session_id}/{step_id}/{variant_type}/{photo.id}.webp"
        }
        
        # Add completed paths for selected images
        if is_selected:
            completed_dir = f"data/photos/generated/completed/{today}"
            os.makedirs(completed_dir, exist_ok=True)
            os.makedirs(f"data/photos/thumbnails/generated/completed/{today}", exist_ok=True)
            
            paths["completed_path"] = f"{completed_dir}/{photo.id}.png"
            paths["completed_thumbnail_path"] = f"data/photos/thumbnails/generated/completed/{today}/{photo.id}.webp"
        
        return paths
    else:
        # Uploaded photos
        upload_dir = f"data/photos/uploaded/{today}"
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(f"data/photos/thumbnails/uploaded/{today}", exist_ok=True)
        
        ext = os.path.splitext(photo.filename)[1].lower() or ".jpg"
        
        return {
            "image_path": f"{upload_dir}/{photo.id}{ext}",
            "thumbnail_path": f"data/photos/thumbnails/uploaded/{today}/{photo.id}.webp"
        }
```

#### 4.2.2 Error Handling Strategy

Implement a consistent error handling pattern:

1. Use specific exception types for different error categories
2. Log detailed error information for debugging
3. Return user-friendly error messages via API
4. Implement appropriate retry mechanisms for transient errors

```python
# Error handling in API layer
@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": {"code": "not_found", "message": str(exc)}}
    )

@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": {"code": "validation_error", "message": str(exc)}}
    )

@app.exception_handler(ConnectionError)
async def connection_error_handler(request, exc):
    return JSONResponse(
        status_code=502,
        content={"error": {"code": "invokeai_connection_error", "message": "Could not connect to InvokeAI backend"}}
    )

@app.exception_handler(GenerationError)
async def generation_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": {"code": "invokeai_generation_error", "message": str(exc)}}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    # Log unexpected exceptions
    logger.exception(f"Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "server_error", "message": "Internal server error"}}
    )
```

#### 4.2.3 Retrieval Retry Management

Implement a robust retry mechanism for failed retrievals:

```python
def retry_failed_retrievals(self, max_attempts=None):
    """Retry all failed retrievals."""
    # Get max attempts from settings if not provided
    if max_attempts is None:
        max_attempts = self.settings_service.get_setting("retrieval_max_attempts", 5)
    
    # Find all photos with failed retrieval status, excluding those exceeding max attempts
    failed_photos = self.db_session.query(Photo).filter(
        Photo.retrieval_status == "failed",
        Photo.retrieval_attempts < max_attempts,
        Photo.invoke_id.isnot(None)
    ).all()
    
    results = {"total": len(failed_photos), "success": 0, "failed": 0}
    
    for photo in failed_photos:
        try:
            success = self.retry_retrieval(photo.id)
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
        except Exception as e:
            logger.error(f"Error retrying retrieval for photo {photo.id}: {e}")
            results["failed"] += 1
    
    return results
```

#### 4.2.4 Background Tasks Management

Implement a simple scheduler for recurring tasks:

```python
def setup_background_tasks(app, photo_service, model_service, backend_manager):
    """Set up background tasks for the application."""
    scheduler = BackgroundScheduler()
    
    # Retry failed retrievals every minute
    scheduler.add_job(
        photo_service.retry_failed_retrievals,
        'interval',
        minutes=1,
        id='retry_retrievals'
    )
    
    # Refresh model cache once a day
    scheduler.add_job(
        model_service.refresh_model_cache,
        'interval',
        days=1,
        id='refresh_models'
    )
    
    # Check idle timeout for remote pods every 5 minutes
    if backend_manager:
        scheduler.add_job(
            backend_manager.check_idle_timeout,
            'interval',
            minutes=5,
            id='check_idle'
        )
    
    # Start the scheduler
    scheduler.start()
    
    # Ensure scheduler shuts down with the application
    @app.on_event("shutdown")
    def shutdown_scheduler():
        scheduler.shutdown()
```

## 5. Code Organization and Best Practices

### 5.1 Project Structure

Follow a clear, modular project structure to make the codebase maintainable:

```
photo_gallery/
├── app/
│   ├── api/                # API routes
│   │   ├── __init__.py
│   │   ├── photos.py       # Photo endpoints
│   │   ├── albums.py       # Album endpoints
│   │   ├── generation.py   # Generation endpoints
│   │   ├── models.py       # Model management endpoints
│   │   ├── settings.py     # Settings endpoints
│   │   └── error_handlers.py  # Centralized error handlers
│   │
│   ├── models/             # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py         # Base model class
│   │   ├── photo.py        # Photo model
│   │   ├── album.py        # Album model
│   │   ├── generation.py   # Generation models
│   │   └── settings.py     # Settings model
│   │
│   ├── services/           # Business logic
│   │   ├── __init__.py
│   │   ├── photo_service.py
│   │   ├── album_service.py
│   │   ├── generation_service.py
│   │   ├── invokeai_client.py
│   │   ├── model_service.py
│   │   ├── file_service.py
│   │   └── settings_service.py
│   │
│   ├── utils/              # Utility functions
│   │   ├── __init__.py
│   │   ├── file_utils.py
│   │   ├── image_utils.py
│   │   ├── error_types.py  # Exception classes
│   │   └── background_tasks.py
│   │
│   ├── __init__.py
│   ├── database.py         # Database connection
│   ├── config.py           # Configuration management
│   └── main.py             # Application entry point
│
├── alembic/                # Database migrations
├── data/                   # Data storage
├── tests/                  # Test files
└── requirements.txt        # Dependencies
```

### 5.2 Code Style Guidelines

Follow these style guidelines for consistent, maintainable code:

1. **Imports Organization**:
   ```python
   # Standard library imports
   import os
   import uuid
   from datetime import datetime
   
   # Third-party imports
   import requests
   from fastapi import APIRouter, Depends, HTTPException
   from sqlalchemy import Column, String
   
   # Application imports
   from app.models.photo import Photo
   from app.utils.error_types import ResourceNotFoundError
   ```

2. **Function Documentation**:
   ```python
   def get_photo_by_id(self, photo_id: UUID) -> Optional[Photo]:
       """
       Get a photo by its ID.
       
       Args:
           photo_id: UUID of the photo to retrieve
           
       Returns:
           Photo object if found, None otherwise
           
       Raises:
           ValueError: If photo_id is None or invalid
       """
       if not photo_id:
           raise ValueError("Photo ID cannot be None")
           
       return self.db_session.query(Photo).filter(Photo.id == photo_id).first()
   ```

3. **Error Handling**:
   ```python
   try:
       photo = self.photo_repository.get_photo_by_id(photo_id)
       if not photo:
           raise ResourceNotFoundError(f"Photo with ID {photo_id} not found")
           
       # Process photo...
       
   except ResourceNotFoundError:
       # Specific handling for known error type
       raise
   except Exception as e:
       # Log and wrap unexpected errors
       logger.exception(f"Unexpected error processing photo {photo_id}: {e}")
       raise PhotoProcessingError(f"Error processing photo: {str(e)}")
   ```

4. **Configuration Management**:
   ```python
   # Use environment variables with defaults
   def get_config(key: str, default=None):
       """Get configuration value with fallback to default."""
       return os.environ.get(key, default)
       
   # Use typed settings
   DATABASE_URL = get_config("DATABASE_URL", "postgresql://postgres:postgres@localhost/photo_gallery")
   MAX_UPLOAD_SIZE = int(get_config("MAX_UPLOAD_SIZE", 20 * 1024 * 1024))  # 20MB
   INVOKEAI_TIMEOUT = int(get_config("INVOKEAI_TIMEOUT", 30))
   ```

### 5.3 Testing Best Practices

1. **Unit Tests**:
   ```python
   def test_photo_service_get_by_id():
       # Arrange
       db_session = create_test_session()
       photo_id = uuid.uuid4()
       test_photo = Photo(id=photo_id, filename="test.jpg", width=100, height=100)
       db_session.add(test_photo)
       db_session.commit()
       
       service = PhotoService(db_session)
       
       # Act
       result = service.get_by_id(photo_id)
       
       # Assert
       assert result is not None
       assert result.id == photo_id
       assert result.filename == "test.jpg"
   ```

2. **Integration Tests**:
   ```python
   def test_upload_photo_endpoint():
       # Arrange
       client = TestClient(app)
       test_image = create_test_image()
       
       # Act
       response = client.post(
           "/api/v1/photos",
           files={"file": ("test.jpg", test_image, "image/jpeg")}
       )
       
       # Assert
       assert response.status_code == 201
       data = response.json()
       assert "id" in data
       assert data["filename"] == "test.jpg"
       assert data["width"] > 0
       assert data["height"] > 0
       
       # Verify file exists
       photo_id = data["id"]
       photo = get_photo_from_db(photo_id)
       assert os.path.exists(photo.local_storage_path)
       assert os.path.exists(photo.local_thumbnail_path)
   ```

3. **InvokeAI Client Tests**:
   ```python
   def test_invokeai_client_queue_generation():
       # Arrange
       client = InvokeAIClient("http://localhost:9090")
       mock_response = httpx.Response(
           201,
           json={"batch_id": "test-batch-123", "success": True}
       )
       
       with patch("httpx.post", return_value=mock_response):
           # Act
           result = client.queue_generation({
               "prompt": "Test prompt",
               "model_key": "test-model",
               "model_hash": "test-hash"
           })
           
           # Assert
           assert result["batch_id"] == "test-batch-123"
           assert result["success"] is True
   ```

### 5.4 Performance Considerations

1. **Database Query Optimization**:
   - Use specific column selection instead of retrieving entire rows
   - Create appropriate indices for common query patterns
   - Use eager loading for relationships when needed

   ```python
   # Instead of this
   photos = session.query(Photo).all()
   
   # Do this for listing
   photos = session.query(
       Photo.id, Photo.filename, Photo.width, Photo.height, 
       Photo.created_at, Photo.is_generated, Photo.thumbnail_path
   ).filter(
       Photo.deleted_at.is_(None)
   ).order_by(
       Photo.created_at.desc()
   ).limit(50).all()
   
   # Use eager loading for relationships
   album_with_photos = session.query(Album).options(
       joinedload(Album.photos)
   ).filter(Album.id == album_id).first()
   ```

2. **Image Processing Efficiency**:
   - Process thumbnails asynchronously when possible
   - Limit maximum dimensions for processing
   - Use efficient image libraries (Pillow with optimization)

   ```python
   def create_thumbnail(self, image_data: bytes, max_size: int = 300) -> bytes:
       """Create an optimized thumbnail from image data."""
       try:
           # Create image from bytes
           image = Image.open(io.BytesIO(image_data))
           
           # Calculate new dimensions while maintaining aspect ratio
           width, height = image.size
           if width > height:
               new_width = min(width, max_size)
               new_height = int(height * (new_width / width))
           else:
               new_height = min(height, max_size)
               new_width = int(width * (new_height / height))
           
           # Resize image using high-quality resampling
           image = image.resize((new_width, new_height), Image.LANCZOS)
           
           # Convert to WebP for better compression
           buffer = io.BytesIO()
           image.save(buffer, 'WEBP', quality=85, optimize=True)
           
           return buffer.getvalue()
       except Exception as e:
           logger.error(f"Error creating thumbnail: {e}")
           raise ValueError(f"Could not create thumbnail: {e}")
   ```

3. **Connection Pooling**:
   - Use connection pooling for database connections
   - Maintain persistent HTTP connections for InvokeAI client
   - Set appropriate timeouts for HTTP requests

   ```python
   # Database connection pool
   engine = create_engine(
       DATABASE_URL,
       pool_size=5,
       max_overflow=10,
       pool_timeout=30,
       pool_recycle=1800
   )
   
   # HTTP client with persistent connections
   http_client = httpx.Client(
       timeout=httpx.Timeout(10.0, read=30.0),
       limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
   )
   ```

## 6. Conclusion

This implementation guide provides practical patterns and examples for implementing the Photo Gallery application with the simplified architecture. By following these guidelines, you can create a maintainable, efficient application that meets the requirements while avoiding unnecessary complexity.

Remember these key principles:
1. Use synchronous operations for simplicity in this single-user application
2. Directly track retrieval status in the photos table
3. Use consistent file organization patterns
4. Implement robust error handling and retry mechanisms
5. Be aware of InvokeAI API limitations and implement appropriate workarounds

For any specific implementation challenges not covered in this guide, refer to the updated system architecture and database schema documents for guidance on the overall approach.