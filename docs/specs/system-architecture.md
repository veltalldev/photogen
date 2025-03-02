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

4. **Simplicity Over Complexity**
   - Favor synchronous operations for single-user application
   - Minimize layers and abstractions
   - Direct tracking over indirect queues
   - Consolidated data models

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

Both modes use the same API-based integration approach, with no direct file system dependencies.

## 2. Technical Infrastructure

### 2.1 Database Architecture

The database uses a simplified schema focused on core entities:

1. **Photos**: Central entity storing all image metadata
2. **Albums**: Collections of photos
3. **Generation Sessions**: Workflows for creating images
4. **Generation Steps**: Individual actions within a session
5. **Models**: Cache of available AI models from InvokeAI
6. **Settings**: Application-wide configuration

The schema follows these design principles:
- Direct tracking of generation and retrieval in photos table
- Consolidated model information in a single table
- Use of JSONB for flexible extension without schema changes
- Appropriate indexing for common access patterns

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
    def __init__(self, db_session, file_service):
        self.db_session = db_session
        self.file_service = file_service
    
    def create(self, file) -> Photo:
        """Create a new photo from uploaded file."""
        # Implementation...
    
    def get(self, id: UUID) -> Optional[Photo]:
        """Get photo by ID."""
        return self.db_session.query(Photo).filter(Photo.id == id).first()
    
    def list(self, filters: Dict) -> List[Photo]:
        """List photos with optional filters."""
        query = self.db_session.query(Photo).filter(Photo.deleted_at.is_(None))
        
        # Apply filters
        if 'generated' in filters:
            query = query.filter(Photo.is_generated == filters['generated'])
        
        if 'album_id' in filters and filters['album_id']:
            query = query.join(AlbumPhoto).filter(AlbumPhoto.album_id == filters['album_id'])
        
        # Apply sorting and pagination
        if 'sort' in filters and filters['sort'] == 'oldest':
            query = query.order_by(Photo.created_at.asc())
        else:
            query = query.order_by(Photo.created_at.desc())
        
        if 'limit' in filters:
            query = query.limit(filters['limit'])
        
        if 'offset' in filters:
            query = query.offset(filters['offset'])
        
        return query.all()
    
    def delete(self, id: UUID) -> bool:
        """Soft-delete a photo."""
        photo = self.get(id)
        if not photo:
            return False
        
        photo.deleted_at = datetime.now()
        self.db_session.commit()
        return True
    
    def update_retrieval_status(self, photo_id: UUID, status: str, error: Optional[str] = None) -> bool:
        """Update retrieval status for a generated photo."""
        photo = self.get(photo_id)
        if not photo:
            return False
        
        photo.retrieval_status = status
        if status == 'failed':
            photo.retrieval_attempts += 1
            photo.last_retrieval_attempt = datetime.now()
            if error:
                photo.retrieval_error = error
        
        self.db_session.commit()
        return True
```

#### Album Service
```python
class AlbumService:
    def __init__(self, db_session):
        self.db_session = db_session
    
    def create(self, name: str, description: Optional[str] = None) -> Album:
        """Create a new album."""
        album = Album(name=name, description=description)
        self.db_session.add(album)
        self.db_session.commit()
        return album
    
    def add_photos(self, id: UUID, photo_ids: List[UUID]) -> bool:
        """Add photos to an album."""
        album = self.db_session.query(Album).get(id)
        if not album:
            return False
        
        # Get current max position
        max_position = self.db_session.query(func.max(AlbumPhoto.position))\
            .filter(AlbumPhoto.album_id == id).scalar() or 0
        
        # Add new photos with incremented positions
        position = max_position + 1
        for photo_id in photo_ids:
            # Check if association already exists
            exists = self.db_session.query(AlbumPhoto)\
                .filter(AlbumPhoto.album_id == id, AlbumPhoto.photo_id == photo_id)\
                .first()
            
            if not exists:
                album_photo = AlbumPhoto(album_id=id, photo_id=photo_id, position=position)
                self.db_session.add(album_photo)
                position += 1
        
        self.db_session.commit()
        return True
```

#### Generation Service
```python
class GenerationService:
    def __init__(self, db_session, invokeai_client, photo_service, file_service):
        self.db_session = db_session
        self.invokeai_client = invokeai_client
        self.photo_service = photo_service
        self.file_service = file_service
    
    def create_session(self, entry_type: str, source_image_id: Optional[UUID] = None) -> GenerationSession:
        """Create a new generation session."""
        session = GenerationSession(
            entry_type=entry_type,
            source_image_id=source_image_id,
            status='active'
        )
        self.db_session.add(session)
        self.db_session.commit()
        return session
    
    def create_step(self, session_id: UUID, params: Dict) -> Tuple[GenerationStep, Dict]:
        """Create and execute a generation step."""
        # Create step record
        step = GenerationStep(
            session_id=session_id,
            parent_id=params.get('parent_id'),
            prompt=params['prompt'],
            negative_prompt=params.get('negative_prompt', ''),
            parameters=params['parameters'],
            model_key=params['model_key'],
            model_hash=params['model_hash'],
            model_name=params.get('model_name', ''),
            position=self._get_next_step_position(session_id),
            status='pending',
            batch_size=params.get('batch_size', 1)
        )
        
        # Generate correlation ID if not provided
        if 'correlation_id' not in params:
            step.correlation_id = str(uuid.uuid4())
        else:
            step.correlation_id = params['correlation_id']
        
        self.db_session.add(step)
        self.db_session.commit()
        
        # Prepare InvokeAI generation parameters
        generation_params = {
            'prompt': step.prompt,
            'negative_prompt': step.negative_prompt,
            'model_key': step.model_key,
            'model_hash': step.model_hash,
            'batch_size': step.batch_size,
            'correlation_id': step.correlation_id,
            **step.parameters  # Include width, height, cfg_scale, etc.
        }
        
        # Submit generation request to InvokeAI
        try:
            response = self.invokeai_client.queue_generation(generation_params)
            
            if 'error' in response:
                step.status = 'failed'
                step.error_message = response['error']
                self.db_session.commit()
                return step, {'error': response['error']}
            
            # Update step with batch ID
            step.batch_id = response['batch_id']
            step.status = 'processing'
            self.db_session.commit()
            
            return step, response
            
        except Exception as e:
            step.status = 'failed'
            step.error_message = str(e)
            self.db_session.commit()
            return step, {'error': str(e)}
    
    def get_step_status(self, step_id: UUID) -> Dict:
        """Get current status of a generation step."""
        step = self.db_session.query(GenerationStep).get(step_id)
        if not step:
            return {'error': 'Step not found'}
        
        # If step is already completed or failed, return current status
        if step.status in ['completed', 'failed']:
            return {
                'id': step.id,
                'status': step.status,
                'batch_id': step.batch_id,
                'error_message': step.error_message,
                'images': self._get_step_images(step.id) if step.status == 'completed' else []
            }
        
        # If step is processing, check batch status from InvokeAI
        if step.status == 'processing' and step.batch_id:
            try:
                batch_status = self.invokeai_client.get_batch_status(step.batch_id)
                
                if batch_status.get('is_complete', False):
                    # Process completed batch
                    return self._process_completed_batch(step, batch_status)
                
                # Still processing
                return {
                    'id': step.id,
                    'status': 'processing',
                    'batch_id': step.batch_id,
                    'progress': batch_status.get('progress', 0)
                }
                
            except Exception as e:
                return {
                    'id': step.id,
                    'status': 'processing',
                    'batch_id': step.batch_id,
                    'error': str(e)
                }
        
        # Default response
        return {
            'id': step.id,
            'status': step.status,
            'batch_id': step.batch_id
        }
    
    def _process_completed_batch(self, step: GenerationStep, batch_status: Dict) -> Dict:
        """Process a completed generation batch and retrieve images."""
        # Get image names from completed batch
        image_names = batch_status.get('image_names', [])
        
        if not image_names:
            step.status = 'failed'
            step.error_message = 'No images were generated'
            self.db_session.commit()
            return {
                'id': step.id,
                'status': 'failed',
                'error_message': 'No images were generated'
            }
        
        # Begin image retrieval process
        retrieved_images = []
        failed_retrievals = 0
        
        for image_name in image_names:
            try:
                # Create photo record for the generated image
                photo = Photo(
                    filename=f"{uuid.uuid4()}.png",
                    width=step.parameters.get('width', 1024),
                    height=step.parameters.get('height', 1024),
                    file_size=0,  # Will update after retrieval
                    mime_type='image/png',
                    is_generated=True,
                    generation_prompt=step.prompt,
                    generation_negative_prompt=step.negative_prompt,
                    generation_params=step.parameters,
                    source_image_id=step.session.source_image_id,
                    invoke_id=image_name,
                    model_key=step.model_key,
                    model_hash=step.model_hash,
                    model_name=step.model_name,
                    retrieval_status='pending'
                )
                
                self.db_session.add(photo)
                self.db_session.commit()
                
                # Create step alternative record
                alternative = StepAlternative(
                    step_id=step.id,
                    image_id=photo.id,
                    selected=False
                )
                
                self.db_session.add(alternative)
                self.db_session.commit()
                
                # Start retrieval in background (could be moved to a worker)
                retrieval_result = self._retrieve_image(image_name, photo.id)
                
                if retrieval_result.get('success', False):
                    retrieved_images.append(retrieval_result['photo'])
                else:
                    failed_retrievals += 1
                
            except Exception as e:
                print(f"Error processing image {image_name}: {e}")
                failed_retrievals += 1
        
        # Update step status
        step.images_retrieved = len(retrieved_images)
        step.images_failed = failed_retrievals
        
        if step.images_retrieved > 0:
            step.status = 'completed'
            step.completed_at = datetime.now()
        else:
            step.status = 'failed'
            step.error_message = 'Failed to retrieve any images'
        
        self.db_session.commit()
        
        # Return status with retrieved images
        return {
            'id': step.id,
            'status': step.status,
            'batch_id': step.batch_id,
            'images': [{'id': img.id, 'thumbnail_url': f"/api/photos/thumbnail/{img.id}"} for img in retrieved_images],
            'retrieval_stats': {
                'total': len(image_names),
                'retrieved': len(retrieved_images),
                'failed': failed_retrievals
            }
        }
    
    def _retrieve_image(self, image_name: str, photo_id: UUID) -> Dict:
        """Retrieve a generated image from InvokeAI."""
        try:
            # Get image data from InvokeAI
            image_data = self.invokeai_client.get_image(image_name)
            thumbnail_data = self.invokeai_client.get_thumbnail(image_name)
            metadata = self.invokeai_client.get_image_metadata(image_name)
            
            # Get photo record
            photo = self.db_session.query(Photo).get(photo_id)
            if not photo:
                return {'success': False, 'error': 'Photo record not found'}
            
            # Create directory structure
            step = self.db_session.query(GenerationStep)\
                .join(StepAlternative)\
                .filter(StepAlternative.image_id == photo_id)\
                .first()
            
            if not step:
                return {'success': False, 'error': 'Step record not found'}
            
            # Generate file paths
            storage_path = self._generate_storage_path(step.session_id, step.id, photo.id)
            thumbnail_path = self._generate_thumbnail_path(step.session_id, step.id, photo.id)
            
            # Save files
            self.file_service.save_file(storage_path, image_data)
            self.file_service.save_file(thumbnail_path, thumbnail_data)
            
            # Update photo record with metadata
            photo.file_size = len(image_data)
            photo.local_storage_path = storage_path
            photo.local_thumbnail_path = thumbnail_path
            photo.retrieval_status = 'completed'
            
            # Update metadata from InvokeAI if available
            if metadata:
                photo.generation_params.update(metadata)
            
            self.db_session.commit()
            
            return {'success': True, 'photo': photo}
            
        except Exception as e:
            # Update photo record with error
            photo = self.db_session.query(Photo).get(photo_id)
            if photo:
                photo.retrieval_status = 'failed'
                photo.retrieval_attempts += 1
                photo.last_retrieval_attempt = datetime.now()
                photo.retrieval_error = str(e)
                self.db_session.commit()
            
            return {'success': False, 'error': str(e)}
    
    def _get_next_step_position(self, session_id: UUID) -> int:
        """Get the next step position for a session."""
        max_position = self.db_session.query(func.max(GenerationStep.position))\
            .filter(GenerationStep.session_id == session_id).scalar()
        
        return 1 if max_position is None else max_position + 1
    
    def _get_step_images(self, step_id: UUID) -> List[Dict]:
        """Get all images associated with a step."""
        alternatives = self.db_session.query(StepAlternative)\
            .filter(StepAlternative.step_id == step_id)\
            .join(Photo)\
            .filter(Photo.retrieval_status == 'completed')\
            .all()
        
        return [
            {
                'id': alt.photo.id,
                'thumbnail_url': f"/api/photos/thumbnail/{alt.photo.id}",
                'selected': alt.selected
            }
            for alt in alternatives
        ]
    
    def _generate_storage_path(self, session_id: UUID, step_id: UUID, photo_id: UUID) -> str:
        """Generate storage path for a generated image."""
        return f"data/photos/generated/sessions/{session_id}/{step_id}/variants/{photo_id}.png"
    
    def _generate_thumbnail_path(self, session_id: UUID, step_id: UUID, photo_id: UUID) -> str:
        """Generate thumbnail path for a generated image."""
        return f"data/photos/thumbnails/generated/sessions/{session_id}/{step_id}/variants/{photo_id}.webp"
```

#### InvokeAI Client
```python
class InvokeAIClient:
    """Client for interacting with InvokeAI API."""
    
    def __init__(self, 
                base_url: str,
                model_service,
                timeout: int = 30):
        """
        Initialize the InvokeAI client.
        
        Args:
            base_url: Base URL for the InvokeAI API
            model_service: Service for model information
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.model_service = model_service
        self.timeout = timeout
        self.connected = False
        self.api_version = None
    
    def connect(self) -> bool:
        """
        Connect to InvokeAI API and verify availability.
        
        Returns:
            bool: True if connection successful
        """
        try:
            response = requests.get(f"{self.base_url}/api/v1/app/version", timeout=self.timeout)
            
            if response.status_code == 200:
                self.connected = True
                self.api_version = response.json().get("version")
                return True
            
            return False
        except Exception as e:
            print(f"Connection error: {e}")
            self.connected = False
            return False
    
    def get_models(self) -> List[Dict]:
        """
        Get list of available models from InvokeAI.
        
        Returns:
            List of available models
        """
        try:
            response = requests.get(f"{self.base_url}/api/v2/models/", timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json().get("models", [])
            
            return []
        except Exception as e:
            print(f"Error getting models: {e}")
            return []
    
    def queue_generation(self, params: Dict) -> Dict:
        """
        Queue a generation request with InvokeAI.
        
        Args:
            params: Generation parameters including prompt, model, dimensions, etc.
        
        Returns:
            Response with batch ID or error information
        """
        # Build the graph structure for InvokeAI
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
                return {"error": f"API error: {response.status_code}", "details": response.text}
                
        except Exception as e:
            return {"error": str(e)}
    
    def get_batch_status(self, batch_id: str) -> Dict:
        """
        Get status of a batch.
        
        Args:
            batch_id: The ID of the batch to check
            
        Returns:
            Current status of the batch
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/queue/default/b/{batch_id}/status",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Calculate overall progress
                total = data.get("total", 0)
                completed = data.get("completed", 0)
                progress = (completed / total) * 100 if total > 0 else 0
                
                # Check if all items are complete
                is_complete = (data.get("completed", 0) + data.get("failed", 0)) == data.get("total", 0)
                
                # Extract image names from completed items
                image_names = []
                if is_complete:
                    for item in data.get("items", []):
                        if item.get("status") == "completed" and "result" in item:
                            image_names.append(item["result"].get("image_name"))
                
                return {
                    "batch_id": batch_id,
                    "status": "completed" if is_complete else "processing",
                    "progress": progress,
                    "is_complete": is_complete,
                    "image_names": image_names
                }
            else:
                return {"error": f"API error: {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def get_image(self, image_name: str) -> bytes:
        """
        Get full-resolution image data.
        
        Args:
            image_name: Name of the image in InvokeAI
            
        Returns:
            Binary image data
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/images/i/{image_name}/full",
                timeout=self.timeout * 2  # Longer timeout for image retrieval
            )
            
            if response.status_code == 200:
                return response.content
            
            raise Exception(f"Failed to retrieve image: {response.status_code}")
            
        except Exception as e:
            raise Exception(f"Error retrieving image: {e}")
    
    def get_thumbnail(self, image_name: str) -> bytes:
        """
        Get thumbnail image data.
        
        Args:
            image_name: Name of the image in InvokeAI
            
        Returns:
            Binary thumbnail data
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/images/i/{image_name}/thumbnail",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.content
            
            raise Exception(f"Failed to retrieve thumbnail: {response.status_code}")
            
        except Exception as e:
            raise Exception(f"Error retrieving thumbnail: {e}")
    
    def get_image_metadata(self, image_name: str) -> Dict:
        """
        Get metadata for a specific image.
        
        Args:
            image_name: Name of the image in InvokeAI
            
        Returns:
            Image metadata dictionary
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/images/i/{image_name}/metadata",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            
            return {}
            
        except Exception as e:
            print(f"Error getting metadata: {e}")
            return {}
    
    def _build_generation_graph(self, params: Dict) -> Dict:
        """
        Build the graph structure for InvokeAI generation.
        
        Args:
            params: Generation parameters
            
        Returns:
            Complete graph structure for InvokeAI API
        """
        # Generate unique IDs for graph nodes
        node_id = self._create_node_id_generator()
        
        # Node IDs
        nodes = {
            "model_loader": node_id("sdxl_model_loader"),
            "pos_prompt": node_id("sdxl_compel_prompt"),
            "neg_prompt": node_id("sdxl_compel_prompt"),
            "pos_collect": node_id("collect"),
            "neg_collect": node_id("collect"),
            "noise": node_id("noise"),
            "denoise": node_id("denoise_latents"),
            "vae_loader": node_id("vae_loader"),
            "metadata": node_id("core_metadata"),
            "output": node_id("l2i")
        }
        
        # Get VAE information
        vae = self.model_service.get_default_vae(params['model_key'])
        if not vae:
            raise ValueError(f"No compatible VAE found for model {params['model_key']}")
        
        # Generate random seed if not provided
        seed = params.get('seed', random.randint(1, 1000000))
        
        # Create graph structure
        graph = {
            "prepend": False,
            "batch": {
                "graph": {
                    "id": f"sdxl_graph_{uuid.uuid4().hex[:8]}",
                    "nodes": {
                        # Model loader node
                        nodes["model_loader"]: {
                            "type": "sdxl_model_loader",
                            "id": nodes["model_loader"],
                            "model": {
                                "key": params['model_key'],
                                "hash": params['model_hash'],
                                "type": "main"
                            },
                            "is_intermediate": True,
                            "use_cache": True
                        },
                        
                        # Prompt nodes and collectors
                        nodes["pos_prompt"]: {
                            "type": "sdxl_compel_prompt",
                            "id": nodes["pos_prompt"],
                            "prompt": params['prompt'],
                            "style": params['prompt'],
                            "is_intermediate": True,
                            "use_cache": True
                        },
                        nodes["pos_collect"]: {
                            "type": "collect",
                            "id": nodes["pos_collect"],
                            "is_intermediate": True,
                            "use_cache": True
                        },
                        nodes["neg_prompt"]: {
                            "type": "sdxl_compel_prompt",
                            "id": nodes["neg_prompt"],
                            "prompt": params.get('negative_prompt', ''),
                            "style": "",
                            "is_intermediate": True,
                            "use_cache": True
                        },
                        nodes["neg_collect"]: {
                            "type": "collect",
                            "id": nodes["neg_collect"],
                            "is_intermediate": True,
                            "use_cache": True
                        },
                        
                        # Noise generator
                        nodes["noise"]: {
                            "type": "noise",
                            "id": nodes["noise"],
                            "seed": seed,
                            "width": params.get('width', 1024),
                            "height": params.get('height', 1024),
                            "use_cpu": True,
                            "is_intermediate": True,
                            "use_cache": True
                        },
                        
                        # Denoiser
                        nodes["denoise"]: {
                            "type": "denoise_latents",
                            "id": nodes["denoise"],
                            "cfg_scale": params.get('cfg_scale', 7.5),
                            "cfg_rescale_multiplier": 0,
                            "scheduler": params.get('scheduler', 'euler'),
                            "steps": params.get('steps', 30),
                            "denoising_start": 0,
                            "denoising_end": 1,
                            "is_intermediate": True,
                            "use_cache": True
                        },
                        
                        # VAE loader
                        nodes["vae_loader"]: {
                            "type": "vae_loader",
                            "id": nodes["vae_loader"],
                            "vae_model": {
                                "key": vae['key'],
                                "hash": vae['hash'],
                                "type": "vae"
                            },
                            "is_intermediate": True,
                            "use_cache": True
                        },
                        
                        # Metadata
                        nodes["metadata"]: {
                            "id": nodes["metadata"],
                            "type": "core_metadata",
                            "is_intermediate": True,
                            "use_cache": True,
                            "generation_mode": "sdxl_txt2img",
                            "cfg_scale": params.get('cfg_scale', 7.5),
                            "cfg_rescale_multiplier": 0,
                            "width": params.get('width', 1024),
                            "height": params.get('height', 1024),
                            "negative_prompt": params.get('negative_prompt', ''),
                            "model": {
                                "key": params['model_key'],
                                "hash": params['model_hash'],
                                "type": "main"
                            },
                            "steps": params.get('steps', 30),
                            "rand_device": "cpu",
                            "scheduler": params.get('scheduler', 'euler'),
                            "vae": {
                                "key": vae['key'],
                                "hash": vae['hash'],
                                "type": "vae"
                            }
                        },
                        
                        # Output
                        nodes["output"]: {
                            "type": "l2i",
                            "id": nodes["output"],
                            "fp32": False,
                            "is_intermediate": False,
                            "use_cache": False
                        }
                    },
                    "edges": [
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
                },
                "runs": 1,
                "data": [
                    [
                        # Seed override for both noise and metadata
                        {"node_path": nodes["noise"], "field_name": "seed", "items": [seed]},
                        {"node_path": nodes["metadata"], "field_name": "seed", "items": [seed]},
                        
                        # Critical: Prompt overrides for metadata preservation
                        {"node_path": nodes["metadata"], "field_name": "positive_prompt", "items": [params['prompt']]},
                        {"node_path": nodes["metadata"], "field_name": "positive_style_prompt", "items": [params['prompt']]}
                    ]
                ],
                "origin": "photo_gallery",
                "destination": "gallery"
            }
        }
        
        # If batch_size > 1, create multiple seeds
        if params.get('batch_size', 1) > 1:
            batch_size = min(params.get('batch_size', 1), 10)  # Cap at 10
            
            if 'seed' in params:
                # Create sequential seeds starting from provided seed
                seeds = [params['seed'] + i for i in range(batch_size)]
            else:
                # Create random seeds
                seeds = [random.randint(1, 1000000) for _ in range(batch_size)]
            
            # Update data section with multiple seeds
            graph["batch"]["data"][0][0]["items"] = seeds  # noise seeds
            graph["batch"]["data"][0][1]["items"] = seeds  # metadata seeds
        
        # Add correlation ID if provided
        if 'correlation_id' in params:
            # Add to prompt for verification
            correlation_marker = f" [CID:{params['correlation_id']}]"
            modified_prompt = params['prompt'] + correlation_marker
            
            # Update prompt node and metadata
            graph["batch"]["data"][0].append({
                "node_path": nodes["pos_prompt"], 
                "field_name": "prompt", 
                "items": [modified_prompt]
            })
            graph["batch"]["data"][0].append({
                "node_path": nodes["metadata"], 
                "field_name": "positive_prompt", 
                "items": [modified_prompt]
            })
        
        return graph
    
    def _create_node_id_generator(self):
        """Create a function that generates unique node IDs."""
        counters = {}
        
        def generate_id(prefix):
            if prefix not in counters:
                counters[prefix] = 0
            counters[prefix] += 1
            return f"{prefix}:{counters[prefix]}"
        
        return generate_id
```

#### Model Service
```python
class ModelService:
    """Service for managing model information and caching."""
    
    def __init__(self, db_session):
        self.db_session = db_session
    
    def refresh_models(self, invokeai_client) -> int:
        """Refresh model cache from InvokeAI."""
        # Get models from InvokeAI
        api_models = invokeai_client.get_models()
        if not api_models:
            return 0
        
        # Process models
        count = 0
        
        for api_model in api_models:
            # Check if model already exists
            model = self.db_session.query(Model).get(api_model.get('key'))
            
            if model:
                # Update existing model
                model.hash = api_model.get('hash', '')
                model.name = api_model.get('name', '')
                model.type = api_model.get('type', '')
                model.base = api_model.get('base', '')
                model.description = api_model.get('description', '')
                
                # Update default parameters if available
                defaults = api_model.get('default_settings', {})
                if defaults:
                    model.default_width = defaults.get('width')
                    model.default_height = defaults.get('height')
                    model.default_steps = defaults.get('steps')
                    model.default_cfg_scale = defaults.get('cfg_scale')
                    model.default_scheduler = defaults.get('scheduler')
                
                # Update timestamp
                model.cached_at = datetime.now()
                
            else:
                # Create new model
                model = Model(
                    key=api_model.get('key'),
                    hash=api_model.get('hash', ''),
                    name=api_model.get('name', ''),
                    type=api_model.get('type', ''),
                    base=api_model.get('base', ''),
                    description=api_model.get('description', ''),
                    cached_at=datetime.now()
                )
                
                # Set default parameters if available
                defaults = api_model.get('default_settings', {})
                if defaults:
                    model.default_width = defaults.get('width')
                    model.default_height = defaults.get('height')
                    model.default_steps = defaults.get('steps')
                    model.default_cfg_scale = defaults.get('cfg_scale')
                    model.default_scheduler = defaults.get('scheduler')
                
                self.db_session.add(model)
                count += 1
        
        # Process VAE compatibility
        for model in self.db_session.query(Model).filter(Model.type == 'vae').all():
            model.compatible_with_base = model.base
        
        # Set default VAEs for each base
        for base in self.db_session.query(func.distinct(Model.base)).all():
            base_name = base[0]
            default_vae = self._find_default_vae_for_base(base_name)
            
            if default_vae:
                default_vae.is_default_vae = True
        
        self.db_session.commit()
        return count
    
    def get_all_models(self, model_type: str = 'main') -> List[Dict]:
        """Get all models of a given type."""
        models = self.db_session.query(Model)\
            .filter(Model.type == model_type)\
            .order_by(Model.is_favorite.desc(), Model.name)\
            .all()
        
        return [self._model_to_dict(model) for model in models]
    
    def get_model(self, key: str) -> Optional[Dict]:
        """Get a specific model by key."""
        model = self.db_session.query(Model).get(key)
        if not model:
            return None
        
        return self._model_to_dict(model)
    
    def get_compatible_vaes(self, model_key: str) -> List[Dict]:
        """Get VAEs compatible with the specified model."""
        model = self.db_session.query(Model).get(model_key)
        if not model:
            return []
        
        # Find VAEs compatible with this model's base
        vaes = self.db_session.query(Model)\
            .filter(Model.type == 'vae',
                    Model.compatible_with_base == model.base)\
            .order_by(Model.is_default_vae.desc(), Model.name)\
            .all()
        
        return [self._model_to_dict(vae) for vae in vaes]
    
    def get_default_vae(self, model_key: str) -> Optional[Dict]:
        """Get the default VAE for the specified model."""
        model = self.db_session.query(Model).get(model_key)
        if not model:
            return None
        
        # Find default VAE for this model's base
        vae = self.db_session.query(Model)\
            .filter(Model.type == 'vae',
                    Model.compatible_with_base == model.base,
                    Model.is_default_vae.is_(True))\
            .first()
        
        if not vae:
            # If no default is set, find any compatible VAE
            vae = self.db_session.query(Model)\
                .filter(Model.type == 'vae',
                        Model.compatible_with_base == model.base)\
                .first()
        
        if not vae:
            return None
        
        return self._model_to_dict(vae)
    
    def add_to_favorites(self, model_key: str) -> bool:
        """Add a model to favorites."""
        model = self.db_session.query(Model).get(model_key)
        if not model:
            return False
        
        model.is_favorite = True
        model.last_used_at = datetime.now()
        self.db_session.commit()
        return True
    
    def remove_from_favorites(self, model_key: str) -> bool:
        """Remove a model from favorites."""
        model = self.db_session.query(Model).get(model_key)
        if not model:
            return False
        
        model.is_favorite = False
        self.db_session.commit()
        return True
    
    def _model_to_dict(self, model: Model) -> Dict:
        """Convert a model entity to a dictionary."""
        return {
            'key': model.key,
            'hash': model.hash,
            'name': model.name,
            'type': model.type,
            'base': model.base,
            'description': model.description,
            'default_width': model.default_width,
            'default_height': model.default_height,
            'default_steps': model.default_steps,
            'default_cfg_scale': model.default_cfg_scale,
            'default_scheduler': model.default_scheduler,
            'is_favorite': model.is_favorite,
            'last_used_at': model.last_used_at,
            'cached_at': model.cached_at
        }
    
    def _find_default_vae_for_base(self, base: str) -> Optional[Model]:
        """Find the best VAE to use as default for a model base."""
        # Look for VAEs with 'fp16-fix' or similar in the name
        vae = self.db_session.query(Model)\
            .filter(Model.type == 'vae',
                    Model.base == base,
                    Model.name.ilike('%fp16%'))\
            .first()
        
        if vae:
            return vae
        
        # Otherwise, just take the first one
        return self.db_session.query(Model)\
            .filter(Model.type == 'vae',
                    Model.base == base)\
            .first()
```

### 2.4 Remote Backend Management

```python
class BackendManager:
    """Manages InvokeAI backend connections and remote pod operations."""
    
    def __init__(self, db_session, settings_service):
        self.db_session = db_session
        self.settings_service = settings_service
        self._invokeai_client = None
    
    def get_client(self) -> InvokeAIClient:
        """Get or create the InvokeAI client instance."""
        if not self._invokeai_client:
            settings = self.settings_service.get_settings()
            
            # Determine which URL to use
            base_url = settings.remote_backend_url if settings.backend_mode == 'remote' else settings.local_backend_url
            
            # Create client
            self._invokeai_client = InvokeAIClient(
                base_url=base_url,
                model_service=ModelService(self.db_session)
            )
        
        return self._invokeai_client
    
    def get_status(self) -> Dict:
        """Get current backend status."""
        settings = self.settings_service.get_settings()
        client = self.get_client()
        
        is_connected = False
        try:
            is_connected = client.connect()
        except Exception:
            pass
        
        status = {
            'mode': settings.backend_mode,
            'url': client.base_url,
            'connected': is_connected,
            'api_version': client.api_version,
        }
        
        # Update settings with connection status
        settings.is_connected = is_connected
        settings.api_version = client.api_version
        if is_connected:
            settings.last_connected_at = datetime.now()
        self.db_session.commit()
        
        # Add remote-specific info
        if settings.backend_mode == 'remote':
            status.update({
                'pod_id': self._extract_pod_id(settings.remote_backend_url),
                'session_start': settings.current_session_start,
                'current_cost': settings.current_session_cost,
                'idle_time': self._calculate_idle_time(settings.last_connected_at)
            })
        
        return status
    
    def switch_mode(self, use_remote: bool) -> Dict:
        """Switch between local and remote backend modes."""
        settings = self.settings_service.get_settings()
        old_mode = settings.backend_mode
        new_mode = 'remote' if use_remote else 'local'
        
        # If no change, just return current status
        if old_mode == new_mode:
            return self.get_status()
        
        # Update mode
        settings.backend_mode = new_mode
        self.db_session.commit()
        
        # Reset client for new mode
        self._invokeai_client = None
        
        # If switching to remote mode, we might need to start a pod
        if new_mode == 'remote' and not settings.remote_backend_url:
            # No URL set yet, just return status
            return {
                'mode': new_mode,
                'connected': False,
                'message': 'Remote mode activated but no pod configured. Please start a pod.'
            }
        
        # Test connection with new mode
        return self.get_status()
    
    def start_remote_pod(self) -> Dict:
        """Start a remote RunPod instance for InvokeAI."""
        settings = self.settings_service.get_settings()
        
        # Ensure we have an API key
        if not settings.runpod_api_key:
            return {'error': 'RunPod API key not configured'}
        
        try:
            # Initialize RunPod client
            client = RunPodClient(api_key=settings.runpod_api_key)
            
            # Select pod type
            pod_type = settings.runpod_pod_type or 'NVIDIA A5000'
            
            # Start pod
            pod = client.create_pod(
                name='InvokeAI-PhotoGallery',
                image_name='invokeai/invokeai:latest',
                gpu_type=pod_type,
                ports='9090:9090'  # Map InvokeAI port
            )
            
            if not pod or 'id' not in pod:
                return {'error': 'Failed to start pod'}
            
            # Wait for pod to reach running state (with timeout)
            timeout = time.time() + 600  # 10 minutes
            pod_id = pod['id']
            estimated_time = 120  # Default estimate: 2 minutes
            
            # Update settings
            settings.remote_backend_url = f"https://{pod_id}-9090.proxy.runpod.net"
            settings.current_session_id = pod_id
            settings.current_session_start = datetime.now()
            settings.current_session_cost = 0.0
            settings.backend_mode = 'remote'
            self.db_session.commit()
            
            # Reset client
            self._invokeai_client = None
            
            # Return while pod is starting
            return {
                'pod_id': pod_id,
                'status': 'starting',
                'estimated_startup_time': estimated_time
            }
            
        except Exception as e:
            return {'error': f'Error starting pod: {str(e)}'}
    
    def stop_remote_pod(self) -> Dict:
        """Stop the current remote pod."""
        settings = self.settings_service.get_settings()
        
        # Ensure we have a pod running
        if not settings.current_session_id:
            return {'error': 'No active pod session'}
        
        # Ensure we have an API key
        if not settings.runpod_api_key:
            return {'error': 'RunPod API key not configured'}
        
        try:
            # Initialize RunPod client
            client = RunPodClient(api_key=settings.runpod_api_key)
            
            # Stop pod
            result = client.stop_pod(pod_id=settings.current_session_id)
            
            if not result.get('success', False):
                return {'error': 'Failed to stop pod'}
            
            # Calculate session duration and cost
            end_time = datetime.now()
            start_time = settings.current_session_start or end_time
            duration_seconds = (end_time - start_time).total_seconds()
            duration_hours = duration_seconds / 3600
            
            # Get hourly rate for pod type (simplified)
            hourly_rate = self._get_hourly_rate(settings.runpod_pod_type)
            session_cost = duration_hours * hourly_rate
            
            # Update lifetime stats
            settings.lifetime_usage_hours += duration_hours
            settings.lifetime_cost += session_cost
            
            # Record final session cost
            settings.current_session_cost = session_cost
            
            # Clear session
            pod_id = settings.current_session_id
            settings.current_session_id = None
            
            # Switch to local mode
            settings.backend_mode = 'local'
            self.db_session.commit()
            
            # Reset client
            self._invokeai_client = None
            
            return {
                'pod_id': pod_id,
                'status': 'stopped',
                'session_duration': int(duration_seconds),
                'session_cost': round(session_cost, 2)
            }
            
        except Exception as e:
            return {'error': f'Error stopping pod: {str(e)}'}
    
    def check_idle_timeout(self) -> Dict:
        """Check if the remote pod should be shut down due to inactivity."""
        settings = self.settings_service.get_settings()
        
        # Only check if in remote mode with an active pod
        if settings.backend_mode != 'remote' or not settings.current_session_id:
            return {'status': 'not_remote'}
        
        # Calculate idle time
        idle_minutes = self._calculate_idle_time(settings.last_connected_at)
        timeout_minutes = settings.idle_timeout_minutes or 30
        
        # Check if we've reached the timeout
        if idle_minutes >= timeout_minutes:
            result = self.stop_remote_pod()
            result['reason'] = 'idle_timeout'
            result['idle_duration_minutes'] = idle_minutes
            return result
        
        # Return current idle status
        return {
            'status': 'active',
            'idle_minutes': idle_minutes,
            'timeout_minutes': timeout_minutes,
            'remaining_minutes': timeout_minutes - idle_minutes
        }
    
    def _calculate_idle_time(self, last_activity: Optional[datetime]) -> int:
        """Calculate minutes since last activity."""
        if not last_activity:
            return 0
        
        delta = datetime.now() - last_activity
        return int(delta.total_seconds() / 60)
    
    def _extract_pod_id(self, url: Optional[str]) -> Optional[str]:
        """Extract pod ID from RunPod URL."""
        if not url:
            return None
        
        # Example URL: https://pod-id-9090.proxy.runpod.net
        match = re.match(r'https://([^-]+)-9090\.proxy\.runpod\.net', url)
        if match:
            return match.group(1)
        
        return None
    
    def _get_hourly_rate(self, pod_type: str) -> float:
        """Get approximate hourly rate for a pod type."""
        rates = {
            'NVIDIA A5000': 0.89,
            'NVIDIA RTX A6000': 1.49,
            'NVIDIA L4': 0.69,
            'NVIDIA RTX 3090': 0.79,
            'NVIDIA RTX 4090': 1.29
        }
        
        return rates.get(pod_type, 1.0)  # Default to $1/hour if unknown
```

## 3. Key Workflows

### 3.1 Generation Workflow

The application implements a linear history model with alternatives:

1. **Session Creation**
   - User starts a new generation session
   - System creates a generation_sessions record
   
2. **Model Selection**
   - User selects a model from available models
   - System identifies compatible VAEs
   - System presents parameter suggestions from model defaults
   
3. **Step Creation**
   - User configures prompt and parameters
   - System generates a correlation ID for tracking
   - System creates a generation_steps record
   - System constructs the graph-based request for InvokeAI
   - System submits request to InvokeAI queue
   - System monitors batch status
   
4. **Image Retrieval**
   - On batch completion, system creates photo records with "pending" status
   - System starts retrieval for each generated image
   - For each successful retrieval:
     - Save image and thumbnail to file system
     - Update photo record with paths and metadata
     - Mark retrieval as "completed"
   - For each failed retrieval:
     - Mark retrieval as "failed" with error message
     - Increment retrieval attempts counter
   
5. **Alternative Selection**
   - User selects preferred image from alternatives
   - System marks selection in step_alternatives
   - If desired, system copies selected image to completed folder
   
6. **Continuation or Completion**
   - User creates new step based on selection or
   - User completes the session
   - System updates status and performs cleanup

### 3.2 Simplified Retrieval Process

The retrieval process is streamlined:

1. **Direct Photo Tracking**
   - Generated photos have retrieval_status field
   - Status transitions: "pending" → "completed" or "failed"
   - Failed retrievals store error message and count attempts
   
2. **Immediate Retrieval**
   - Retrieval is attempted immediately after batch completion
   - Each image has its own photo record with invoke_id for reference
   - Successful retrievals update photo with local file paths
   
3. **Retry Mechanism**
   - Background task periodically checks for failed retrievals
   - Photos with retrieval_status="failed" are retried
   - Retry attempts respect max_retrieval_attempts setting
   
4. **Correlation Strategies**
   - Timestamp-based: Find images created after batch start time
   - Correlation ID: Embed and verify ID in prompt metadata

### 3.3 Backend Management

The application supports two backend modes:

1. **Local Mode**
   - Direct connection to localhost:9090
   - No additional management required
   - User responsible for starting/stopping InvokeAI

2. **Remote Mode (RunPod)**
   - On-demand startup of InvokeAI instance
   - Cost tracking based on usage time
   - Idle timeout detection and automatic shutdown
   - Session history with cost metrics

## 4. Implementation Guidelines

### 4.1 Code Organization

```
app/
├── api/                  # FastAPI route definitions
│   ├── photos.py
│   ├── albums.py
│   ├── sharing.py
│   ├── generation.py
│   └── backend.py
├── models/               # SQLAlchemy models
│   ├── photo.py
│   ├── album.py
│   ├── generation.py
│   ├── model_cache.py
│   └── settings.py
├── services/             # Business logic services
│   ├── photo_service.py
│   ├── album_service.py
│   ├── generation_service.py
│   ├── invokeai_client.py
│   ├── model_service.py
│   └── backend_manager.py
├── repositories/         # Data access layer
│   ├── photo_repository.py
│   ├── album_repository.py
│   └── generation_repository.py
├── utils/                # Utility functions
│   ├── file_utils.py
│   ├── image_utils.py
│   ├── storage.py
│   └── error_handling.py
└── main.py               # Application entry point
```

### 4.2 Error Handling

```python
# Define custom exceptions
class InvokeAIError(Exception):
    """Base class for InvokeAI-related errors."""
    pass

class ConnectionError(InvokeAIError):
    """Error connecting to InvokeAI."""
    pass

class ModelError(InvokeAIError):
    """Error related to model handling."""
    pass

class GenerationError(InvokeAIError):
    """Error during image generation."""
    pass

class RetrievalError(InvokeAIError):
    """Error retrieving generated images."""
    pass

# Global error handler
class ErrorHandler:
    @staticmethod
    def handle_invokeai_error(e: Exception) -> Dict:
        """Convert exceptions to standardized error responses."""
        if isinstance(e, ConnectionError):
            return {
                "code": "connection_error",
                "message": "Could not connect to InvokeAI backend",
                "details": str(e)
            }
        elif isinstance(e, ModelError):
            return {
                "code": "model_error",
                "message": "Error with AI model",
                "details": str(e)
            }
        elif isinstance(e, GenerationError):
            return {
                "code": "generation_error",
                "message": "Error during image generation",
                "details": str(e)
            }
        elif isinstance(e, RetrievalError):
            return {
                "code": "retrieval_error",
                "message": "Error retrieving generated images",
                "details": str(e)
            }
        else:
            return {
                "code": "unknown_error",
                "message": "An unexpected error occurred",
                "details": str(e)
            }
```

### 4.3 Background Tasks

Background tasks handle recurring operations:

```python
# Task scheduler
class BackgroundTaskManager:
    def __init__(self):
        self.tasks = []
        self.scheduler = None
    
    def add_task(self, name: str, interval: int, func: Callable, *args, **kwargs):
        """Add a background task to the scheduler."""
        task = {
            "name": name,
            "interval": interval,
            "func": func,
            "args": args,
            "kwargs": kwargs,
            "last_run": None,
            "next_run": datetime.now()
        }
        self.tasks.append(task)
    
    async def run_tasks(self):
        """Run due tasks."""
        now = datetime.now()
        
        for task in self.tasks:
            if now >= task["next_run"]:
                try:
                    # Run the task
                    result = task["func"](*task["args"], **task["kwargs"])
                    
                    # If it's a coroutine, await it
                    if asyncio.iscoroutine(result):
                        await result
                    
                    # Update task timing
                    task["last_run"] = now
                    task["next_run"] = now + timedelta(seconds=task["interval"])
                    
                except Exception as e:
                    print(f"Error in background task {task['name']}: {e}")
    
    async def start_scheduler(self):
        """Start the background task scheduler."""
        self.scheduler = asyncio.create_task(self._scheduler_loop())
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while True:
            await self.run_tasks()
            await asyncio.sleep(1)  # Check every second
    
    def stop_scheduler(self):
        """Stop the scheduler."""
        if self.scheduler:
            self.scheduler.cancel()
```

Example background tasks:

```python
# Set up background tasks
task_manager = BackgroundTaskManager()

# Retry failed retrievals every minute
task_manager.add_task(
    "retry_failed_retrievals",
    60,
    photo_service.retry_failed_retrievals,
    max_attempts=5
)

# Refresh model cache every 15 minutes
task_manager.add_task(
    "refresh_model_cache",
    900,
    model_service.refresh_models,
    invokeai_client
)

# Check for idle pod shutdown every 5 minutes
task_manager.add_task(
    "check_idle_timeout",
    300,
    backend_manager.check_idle_timeout
)
```

### 4.4 File Management

```python
class FileService:
    """Manages file storage and organization."""
    
    def __init__(self, base_dir: str = 'data'):
        self.base_dir = base_dir
    
    def save_file(self, path: str, content: bytes) -> bool:
        """Save file to disk."""
        try:
            # Create directory structure if needed
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Write file
            with open(path, 'wb') as f:
                f.write(content)
            
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False
    
    def read_file(self, path: str) -> Optional[bytes]:
        """Read file from disk."""
        try:
            with open(path, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return None
    
    def delete_file(self, path: str) -> bool:
        """Delete file from disk."""
        try:
            if os.path.exists(path):
                os.remove(path)
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    def generate_upload_path(self, filename: str) -> str:
        """Generate path for uploaded file."""
        today = datetime.now().strftime("%Y-%m-%d")
        ext = os.path.splitext(filename)[1].lower()
        unique_name = f"{uuid.uuid4()}{ext}"
        
        return f"{self.base_dir}/photos/uploaded/{today}/{unique_name}"
    
    def generate_thumbnail_path(self, original_path: str) -> str:
        """Generate thumbnail path for an image."""
        # Replace file extension with .webp
        path_parts = original_path.rsplit('.', 1)
        base_path = path_parts[0]
        
        # Replace /photos/ with /thumbnails/
        thumb_path = base_path.replace('/photos/', '/photos/thumbnails/') + '.webp'
        
        return thumb_path
    
    def create_thumbnail(self, image_data: bytes, max_size: int = 300) -> bytes:
        """Create a thumbnail from image data."""
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
            
            # Resize image
            image = image.resize((new_width, new_height), Image.LANCZOS)
            
            # Convert to WebP
            buffer = io.BytesIO()
            image.save(buffer, 'WEBP', quality=85)
            
            return buffer.getvalue()
            
        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            raise ValueError(f"Could not create thumbnail: {e}")
```

## 5. API Endpoints

### 5.1 Core Photo Endpoints

```python
@router.get("/photos")
def list_photos(
    limit: int = 50,
    offset: int = 0,
    generated: Optional[bool] = None,
    album_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """List photos with optional filtering."""
    filters = {
        "limit": limit,
        "offset": offset
    }
    
    if generated is not None:
        filters["generated"] = generated
    
    if album_id:
        filters["album_id"] = album_id
    
    photo_service = PhotoService(db)
    photos = photo_service.list(filters)
    
    return {
        "items": [photo.to_dict() for photo in photos],
        "total": photo_service.count(filters),
        "limit": limit,
        "offset": offset
    }

@router.get("/photos/{id}")
def get_photo(id: UUID, db: Session = Depends(get_db)):
    """Get a specific photo."""
    photo_service = PhotoService(db)
    photo = photo_service.get(id)
    
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    return FileResponse(
        photo.local_storage_path,
        media_type=photo.mime_type,
        filename=photo.filename
    )

@router.get("/photos/thumbnail/{id}")
def get_thumbnail(id: UUID, db: Session = Depends(get_db)):
    """Get a photo thumbnail."""
    photo_service = PhotoService(db)
    photo = photo_service.get(id)
    
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    if not photo.local_thumbnail_path:
        raise HTTPException(status_code=404, detail="Thumbnail not available")
    
    return FileResponse(
        photo.local_thumbnail_path,
        media_type="image/webp"
    )

@router.post("/photos")
def upload_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a new photo."""
    photo_service = PhotoService(db)
    try:
        photo = photo_service.create(file)
        return photo.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/photos/{id}")
def delete_photo(id: UUID, db: Session = Depends(get_db)):
    """Delete a photo (soft delete)."""
    photo_service = PhotoService(db)
    success = photo_service.delete(id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    return {"success": True}

@router.post("/photos/{id}/retry")
def retry_photo_retrieval(id: UUID, db: Session = Depends(get_db)):
    """Retry retrieving a generated photo."""
    photo_service = PhotoService(db)
    result = photo_service.retry_retrieval(id)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result
```

### 5.2 Generation Endpoints

```python
@router.post("/generation/sessions")
def create_session(
    data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """Create a new generation session."""
    generation_service = GenerationService(db)
    
    entry_type = data.get("entry_type", "scratch")
    source_image_id = data.get("source_image_id")
    
    # Validate source image if provided
    if source_image_id:
        photo_service = PhotoService(db)
        photo = photo_service.get(source_image_id)
        if not photo:
            raise HTTPException(status_code=404, detail="Source image not found")
    
    # Create session
    session = generation_service.create_session(
        entry_type=entry_type,
        source_image_id=source_image_id
    )
    
    return session.to_dict()

@router.post("/generation/sessions/{session_id}/steps")
def create_step(
    session_id: UUID,
    data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """Create and execute a generation step."""
    generation_service = GenerationService(db)
    
    # Verify session exists
    session = generation_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Validate required fields
    if not data.get("prompt"):
        raise HTTPException(status_code=400, detail="Prompt is required")
    
    if not data.get("model_key"):
        raise HTTPException(status_code=400, detail="Model key is required")
    
    # Create step
    try:
        step, response = generation_service.create_step(session_id, data)
        
        if "error" in response:
            raise HTTPException(status_code=400, detail=response["error"])
        
        return {
            "id": step.id,
            "session_id": session_id,
            "batch_id": step.batch_id,
            "status": step.status
        }
        
    except Exception as e:
        error_response = ErrorHandler.handle_invokeai_error(e)
        raise HTTPException(status_code=400, detail=error_response)

@router.get("/generation/steps/{step_id}/status")
def get_step_status(step_id: UUID, db: Session = Depends(get_db)):
    """Get current status of a generation step."""
    generation_service = GenerationService(db)
    
    status = generation_service.get_step_status(step_id)
    
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    
    return status

@router.post("/generation/steps/{step_id}/select")
def select_alternative(
    step_id: UUID,
    data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """Select a preferred image from step alternatives."""
    generation_service = GenerationService(db)
    
    image_id = data.get("image_id")
    if not image_id:
        raise HTTPException(status_code=400, detail="Image ID is required")
    
    success = generation_service.select_alternative(step_id, image_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Step or image not found")
    
    return {"success": True}

@router.post("/generation/steps/{step_id}/retry-retrievals")
def retry_step_retrievals(step_id: UUID, db: Session = Depends(get_db)):
    """Retry failed image retrievals for a step."""
    generation_service = GenerationService(db)
    
    result = generation_service.retry_step_retrievals(step_id)
    
    return result
```

### 5.3 Backend Management Endpoints

```python
@router.get("/backend/status")
def get_backend_status(db: Session = Depends(get_db)):
    """Get current backend connection status."""
    backend_manager = BackendManager(db)
    
    return backend_manager.get_status()

@router.post("/backend/mode")
def set_backend_mode(
    data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """Switch between local and remote backend modes."""
    backend_manager = BackendManager(db)
    
    use_remote = data.get("mode") == "remote"
    result = backend_manager.switch_mode(use_remote)
    
    return result

@router.post("/backend/pod/start")
def start_remote_pod(db: Session = Depends(get_db)):
    """Start a remote pod for InvokeAI."""
    backend_manager = BackendManager(db)
    
    result = backend_manager.start_remote_pod()
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.post("/backend/pod/stop")
def stop_remote_pod(db: Session = Depends(get_db)):
    """Stop the current remote pod."""
    backend_manager = BackendManager(db)
    
    result = backend_manager.stop_remote_pod()
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result
```

## 6. Simplified Deployment

### 6.1 Requirements

- Local machine installation
- PostgreSQL database
- Python 3.10+
- Local InvokeAI instance (optional)
- RunPod API key (for remote mode)

### 6.2 Configuration

Environment variables for local development:

```
# Database
DATABASE_URL=postgresql://user:password@localhost/photo_gallery_dev

# InvokeAI
INVOKEAI_LOCAL_URL=http://localhost:9090
INVOKEAI_CONNECTION_TIMEOUT=10
INVOKEAI_READ_TIMEOUT=30

# RunPod (optional)
RUNPOD_API_KEY=your_api_key_here
RUNPOD_POD_TYPE=NVIDIA A5000
RUNPOD_IDLE_TIMEOUT=30

# Application
MAX_UPLOAD_SIZE=20971520  # 20MB
MAX_BATCH_SIZE=10
RETRIEVAL_MAX_ATTEMPTS=5
```

### 6.3 Startup Sequence

1. Start PostgreSQL
2. Start local InvokeAI (if using local mode)
3. Start application:
   ```bash
   uvicorn app.main:app --reload
   ```

### 6.4 Monitoring

- Application logs for error tracking
- Background task reports
- Cost tracking for remote mode

## 7. Security Considerations

### 7.1 File Validation

```python
def validate_image_file(file: UploadFile) -> bool:
    """Validate an image file for security and compatibility."""
    # Check file extension
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.heic']
    file_ext = os.path.splitext(file.filename.lower())[1]
    
    if file_ext not in valid_extensions:
        raise ValueError(f"Unsupported file type: {file_ext}")
    
    # Limit file size (20MB)
    max_size = 20 * 1024 * 1024  # 20MB
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset position
    
    if file_size > max_size:
        raise ValueError(f"File too large: {file_size} bytes (max {max_size})")
    
    # Verify file is a valid image by opening it
    try:
        image_data = file.file.read()
        image = Image.open(io.BytesIO(image_data))
        file.file.seek(0)  # Reset position
        
        # Check image dimensions
        width, height = image.size
        max_dimension = 8192
        min_dimension = 100
        
        if width > max_dimension or height > max_dimension:
            raise ValueError(f"Image dimensions too large: {width}x{height}")
        
        if width < min_dimension or height < min_dimension:
            raise ValueError(f"Image dimensions too small: {width}x{height}")
        
        return True
        
    except Exception as e:
        raise ValueError(f"Invalid image file: {str(e)}")
```

### 7.2 Share Links

```python
def generate_share_token() -> str:
    """Generate a secure random token for share links."""
    # Generate 32 bytes of random data
    random_bytes = os.urandom(32)
    # Convert to URL-safe base64
    token = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
    # Remove padding characters
    token = token.rstrip('=')
    return token
```

## 8. Testing Strategy

### 8.1 Unit Tests

Focus on testing individual components:

```python
def test_photo_service_create():
    """Test photo creation functionality."""
    # Setup
    db_session = create_test_session()
    file_service = create_mock_file_service()
    photo_service = PhotoService(db_session, file_service)
    
    test_file = create_test_image_file()
    
    # Execute
    photo = photo_service.create(test_file)
    
    # Verify
    assert photo is not None
    assert photo.filename is not None
    assert photo.width > 0
    assert photo.height > 0
    assert not photo.is_generated
    assert photo.local_storage_path is not None
    assert photo.local_thumbnail_path is not None
```

### 8.2 Mock InvokeAI Client

```python
class MockInvokeAIClient:
    """Mock implementation of InvokeAI client for testing."""
    
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.connected = False
        self.api_version = "1.0.0-mock"
        self.requests = []
        self.models = self._create_mock_models()
        self.batches = {}
    
    def connect(self) -> bool:
        """Mock connection to InvokeAI."""
        if self.should_fail:
            self.connected = False
            return False
        
        self.connected = True
        return True
    
    def get_models(self) -> List[Dict]:
        """Get mock models."""
        if self.should_fail:
            return []
        
        return self.models
    
    def queue_generation(self, params: Dict) -> Dict:
        """Mock generation request."""
        self.requests.append(params)
        
        if self.should_fail:
            return {"error": "Mock error"}
        
        # Create mock batch
        batch_id = f"mock-batch-{len(self.batches)}"
        self.batches[batch_id] = {
            "status": "pending",
            "params": params,
            "images": []
        }
        
        # Simulate batch completion after a short delay
        threading.Timer(0.5, self._complete_batch, args=[batch_id]).start()
        
        return {
            "batch_id": batch_id,
            "success": True
        }
    
    def _complete_batch(self, batch_id: str):
        """Simulate batch completion."""
        batch = self.batches.get(batch_id)
        if not batch:
            return
        
        # Generate mock images
        batch_size = batch["params"].get("batch_size", 1)
        for i in range(batch_size):
            image_name = f"mock-image-{batch_id}-{i}"
            batch["images"].append(image_name)
        
        # Mark batch as completed
        batch["status"] = "completed"
    
    def get_batch_status(self, batch_id: str) -> Dict:
        """Get mock batch status."""
        batch = self.batches.get(batch_id)
        if not batch:
            return {"error": "Batch not found"}
        
        is_complete = batch["status"] == "completed"
        
        return {
            "batch_id": batch_id,
            "status": batch["status"],
            "progress": 100 if is_complete else 50,
            "is_complete": is_complete,
            "image_names": batch["images"] if is_complete else []
        }
    
    def get_image(self, image_name: str) -> bytes:
        """Get mock image data."""
        if self.should_fail:
            raise Exception("Mock retrieval error")
        
        # Create a simple image
        img = Image.new('RGB', (100, 100), color=(73, 109, 137))
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()
    
    def get_thumbnail(self, image_name: str) -> bytes:
        """Get mock thumbnail data."""
        if self.should_fail:
            raise Exception("Mock retrieval error")
        
        # Create a simple image
        img = Image.new('RGB', (50, 50), color=(73, 109, 137))
        buf = io.BytesIO()
        img.save(buf, format='WEBP')
        return buf.getvalue()
    
    def get_image_metadata(self, image_name: str) -> Dict:
        """Get mock image metadata."""
        if self.should_fail:
            return {}
        
        return {
            "prompt": "Mock prompt",
            "negative_prompt": "Mock negative prompt",
            "seed": 12345,
            "width": 100,
            "height": 100,
            "cfg_scale": 7.5,
            "steps": 30
        }
    
    def _create_mock_models(self) -> List[Dict]:
        """Create mock model data."""
        return [
            {
                "key": "mock-model-1",
                "hash": "mock-hash-1",
                "name": "Mock Model 1",
                "type": "main",
                "base": "sdxl",
                "default_settings": {
                    "width": 1024,
                    "height": 1024,
                    "steps": 30,
                    "cfg_scale": 7.5,
                    "scheduler": "euler"
                }
            },
            {
                "key": "mock-vae-1",
                "hash": "mock-vae-hash-1",
                "name": "Mock VAE 1",
                "type": "vae",
                "base": "sdxl"
            }
        ]
```

### 8.3 Integration Testing

```python
async def test_generation_workflow():
    """Test complete generation workflow."""
    # Setup application
    app = create_test_app(mock_invokeai=True)
    client = TestClient(app)
    
    # 1. Create session
    session_response = client.post(
        "/api/generation/sessions",
        json={"entry_type": "scratch"}
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["id"]
    
    # 2. Create step
    step_response = client.post(
        f"/api/generation/sessions/{session_id}/steps",
        json={
            "prompt": "Test prompt",
            "model_key": "mock-model-1",
            "model_hash": "mock-hash-1",
            "width": 512,
            "height": 512,
            "steps": 30,
            "cfg_scale": 7.5,
            "batch_size": 2
        }
    )
    assert step_response.status_code == 200
    step_id = step_response.json()["id"]
    
    # 3. Wait for step completion
    max_attempts = 10
    for _ in range(max_attempts):
        status_response = client.get(f"/api/generation/steps/{step_id}/status")
        status = status_response.json()
        
        if status["status"] == "completed":
            break
            
        time.sleep(0.5)
    
    assert status["status"] == "completed"
    assert len(status["images"]) > 0
    
    # 4. Select an alternative
    image_id = status["images"][0]["id"]
    select_response = client.post(
        f"/api/generation/steps/{step_id}/select",
        json={"image_id": image_id}
    )
    assert select_response.status_code == 200
    
    # 5. Complete session
    complete_response = client.patch(
        f"/api/generation/sessions/{session_id}",
        json={"status": "completed"}
    )
    assert complete_response.status_code == 200
```"