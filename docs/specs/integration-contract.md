# Updated InvokeAI Integration Contract Specification

## 1. Overview

This document defines the simplified integration contract between the Photo Gallery application and InvokeAI instances (both local and remote). It has been revised to prioritize simplicity and direct tracking for a single-user application, reducing the layers of abstraction and complexity.

## 2. Connection Management

### 2.1 Backend URL Formation

**Local Mode**: 
- Base URL: `http://localhost:9090`
- No authentication required
- Direct connection to local InvokeAI instance

**Remote Mode**:
- Base URL: `https://{pod-id}-9090.proxy.runpod.net` 
- No authentication required for API access
- RunPod API key required for pod management (separate from InvokeAI access)

### 2.2 Connection Testing

**Health Check Endpoint**:
- `GET /api/v1/app/version`
- Expected response includes version information:
  ```json
  {
    "version": "3.2.0",
    "highlights": ["SDXL support", "Improved UI"]
  }
  ```
- Use this endpoint for:
  - Initial connection validation
  - Health monitoring
  - Checking if the service is ready before submitting generation requests

### 2.3 Backend Status Management

Implement a simplified status monitoring approach:

1. **Connection Status**:
   - Check connection before critical operations
   - Store connection status in application_settings table
   - Update timestamp of last successful connection

2. **Pod Status** (Remote Mode):
   - Track pod status in application_settings table
   - Record session start time and session ID
   - Track approximate cost based on time used

3. **Idle Detection**:
   - Use last_connected_at timestamp to calculate idle time
   - Compare against configured idle_timeout_minutes
   - Implement simple shutdown for inactive pods

## 3. API Integration Points

### 3.1 Model Management

**Listing Available Models**:
- `GET /api/v2/models/` - Returns all available models
- **Critical**: Models have unique UUID keys and hash values that must be saved and used in generation requests
- Example response:
  ```json
  {
    "models": [
      {
        "key": "ece5fa0b-5d3d-4bc4-9912-5caf6d270f53",
        "hash": "blake3:3b49eb5f584e69ad7a09b535ad163a60ed0c912159fac5434d3fdc2a0a88b7ef",
        "name": "kokioIllu_v20",
        "base": "sdxl",
        "type": "main",
        "description": "Anime-style illustration model"
      },
      {
        "key": "c2079afa-3fa5-477c-b10b-1be1e509933e",
        "hash": "blake3:9b7c3120af571e8d93fa82d50ef3b5f15727507d0edaae822424951937a008a3",
        "name": "sdxl-vae-fp16-fix",
        "base": "sdxl",
        "type": "vae"
      }
    ]
  }
  ```

**Model Management Strategy**:
1. Store models in the models table with their key, hash, name, type, and base
2. For VAEs, store the compatible_with_base field to indicate which model base they work with
3. Mark one VAE per base as is_default_vae for automatic selection
4. Refresh model cache periodically (daily or on restart)

### 3.2 Generation Queue

**Submitting Generation Request**:
- `POST /api/v1/queue/{queue_id}/enqueue_batch` - Queue a new generation batch
- Use `default` for queue_id in most cases
- Request must include complete graph structure (see Section 5)
- **Critical**: Include both model key and hash in request

**Batch Status Monitoring**:
- `GET /api/v1/queue/{queue_id}/b/{batch_id}/status` - Specific batch status
- Implement simple polling with increasing intervals (2s, 3s, 5s, 8s, 10s max)
- Extract image names from completed items in the batch

### 3.3 Image Retrieval

**Retrieving Image Content**:
- `GET /api/v1/images/i/{image_name}/metadata` - Image metadata
- `GET /api/v1/images/i/{image_name}/full` - Full-resolution image
- `GET /api/v1/images/i/{image_name}/thumbnail` - Image thumbnail

**Direct Tracking**:
- Track retrieval status directly in photos table
- Update retrieval_status field as images are processed
- Count retrieval attempts and log errors for failed retrievals

**Listing Recent Images** (alternative approach):
- `GET /api/v1/images/?limit={n}` - Get most recent n images
- Use this to verify batch results by comparing timestamps

## 4. Image Retrieval Process

### 4.1 Direct Retrieval Workflow

After batch completion, implement this simplified process:

1. **Create Photo Records**:
   - For each image in the completed batch, create a photo record
   - Set retrieval_status to 'pending'
   - Store invoke_id for reference

2. **Retrieve and Store Images**:
   - For each pending photo:
     - Create appropriate directory structure
     - Download full image using invoke_id
     - Create or download thumbnail
     - Retrieve and store metadata 
     - Update photo record with paths and metadata
     - Change retrieval_status to 'completed'

3. **Error Handling**:
   - If retrieval fails, set retrieval_status to 'failed'
   - Increment retrieval_attempts counter
   - Store error message in retrieval_error field
   - Schedule retry through background task

### 4.2 Retry Mechanism

Implement a simple retry system:

1. **Background Task**:
   - Periodically check for photos with retrieval_status='failed'
   - Retry based on configured settings (max attempts, delay)

2. **Manual Retry**:
   - Provide API endpoint to retry specific failed retrievals
   - Reset retrieval status and attempt immediately

### 4.3 File Organization

Generate file paths based on session and step structure:

```
/data/photos/generated/sessions/{session_id}/{step_id}/variants/{photo_id}.png
/data/photos/thumbnails/generated/sessions/{session_id}/{step_id}/variants/{photo_id}.webp
```

For selected images, also store a copy in the completed directory:

```
/data/photos/generated/completed/{yyyy-mm-dd}/{photo_id}.png
/data/photos/thumbnails/generated/completed/{yyyy-mm-dd}/{photo_id}.webp
```

## 5. Graph Structure for Generation

### 5.1 Complete Graph Structure

The InvokeAI API uses a directed acyclic graph (DAG) to define the generation process. Here's the essential structure:

```json
{
  "prepend": false,
  "batch": {
    "graph": {
      "id": "sdxl_graph:unique_id",
      "nodes": {
        // Node definitions
      },
      "edges": [
        // Edge connections
      ]
    },
    "runs": 1,
    "data": [
      [
        // Data overrides
      ]
    ],
    "origin": "photo_gallery",
    "destination": "gallery"
  }
}
```

### 5.2 Required Nodes

A complete graph must include these node types:

1. **Model Loader** (`sdxl_model_loader`):
   - Loads the main diffusion model
   - Must include exact model key and hash

2. **Prompt Processors** (`sdxl_compel_prompt`):
   - Process positive and negative prompts
   - Two separate nodes needed (positive and negative)

3. **Conditioning Collectors** (`collect`):
   - Aggregate conditioning information
   - Two needed (one for positive, one for negative)

4. **Noise Generator** (`noise`):
   - Creates initial noise with specified seed
   - Controls image dimensions

5. **Latent Denoiser** (`denoise_latents`):
   - Core generation process
   - Controls steps, cfg_scale, and scheduler

6. **VAE Loader** (`vae_loader`):
   - Loads VAE model
   - Must include exact VAE key and hash

7. **Metadata** (`core_metadata`):
   - Records generation parameters
   - **Critical**: Must be explicitly populated in data section

8. **Output Processor** (`l2i` - latents to image):
   - Converts latents to final image
   - Controls output format

### 5.3 Node Connections (Edges)

Edges define how data flows between nodes. Required connections:

1. Model loader to denoise latents (unet)
2. Model loader to prompt processors (clip and clip2)
3. Prompt processors to conditioning collectors
4. Conditioning collectors to denoise latents
5. Noise generator to denoise latents
6. Denoise latents to output processor
7. VAE loader to output processor
8. Metadata to output processor

### 5.4 Metadata Propagation

**Critical Requirement**: To ensure complete metadata in the output image:

1. Set prompt values in the prompt node definitions
2. **AND** also set them explicitly in the data section overrides for the metadata node

Example data section:
```json
"data": [
  [
    {"node_path": "noise:1", "field_name": "seed", "items": [123456]},
    {"node_path": "core_metadata:1", "field_name": "seed", "items": [123456]},
    {"node_path": "core_metadata:1", "field_name": "positive_prompt", "items": ["Mountain landscape with lake"]},
    {"node_path": "core_metadata:1", "field_name": "positive_style_prompt", "items": ["Mountain landscape with lake"]}
  ]
]
```

This ensures prompt information is preserved in the final metadata.

### 5.5 Correlation ID Embedding

To correlate generated images with a specific request:

1. Add a correlation ID to the parameters (can be any unique string)
2. Modify the prompt in the data section by appending a marker: `[CID:correlation_id]`
3. Check this marker in image metadata during retrieval for verification

Example:
```json
{"node_path": "pos_prompt", "field_name": "prompt", "items": ["Mountain landscape [CID:abc123]"]},
{"node_path": "core_metadata", "field_name": "positive_prompt", "items": ["Mountain landscape [CID:abc123]"]}
```

## 6. Common Error Patterns

### 6.1 Network and Connection Errors

1. **Connection Refused**: InvokeAI server is not running
   - Error: `ConnectionRefusedError: [Errno 111] Connection refused`
   - Solution: Start InvokeAI server or check URL and port

2. **Timeout Errors**: Server is busy or unresponsive
   - Error: `TimeoutError: Connection timeout`
   - Solution: Increase timeout value, check server load

3. **DNS Resolution Errors**: Invalid hostname (remote mode)
   - Error: `gaierror: [Errno -2] Name or service not known`
   - Solution: Check remote URL configuration

### 6.2 API-Related Errors

1. **Invalid Model Key**: Model doesn't exist
   - Error: `"detail": "Model with key 'invalid_model' not found"`
   - Solution: Use valid model key from `/api/v2/models/`

2. **Invalid Graph Structure**: Missing required connections
   - Error: `"detail": "Missing required connection for node 'denoise_latents:1'"`
   - Solution: Ensure graph has all required connections

3. **Parameter Validation Errors**: Invalid parameter values
   - Error: `"detail": "Value error, cfg_scale must be greater than 1.0"`
   - Solution: Ensure parameters meet requirements

4. **Resource Limitations**: Insufficient GPU memory
   - Error: `"detail": "CUDA out of memory"`
   - Solution: Reduce image dimensions or batch size

### 6.3 Error Handling Strategy

1. **Categorize Errors**:
   - InvokeAIError as base exception class
   - ConnectionError for connectivity issues
   - ModelError for model-related issues 
   - GenerationError for graph and parameter issues
   - RetrievalError for image retrieval issues

2. **Error Logging**:
   - Log detailed error information
   - Include context (batch ID, image name, etc.)
   - Store error messages in database for review

3. **User Feedback**:
   - Map technical errors to user-friendly messages
   - Provide specific guidance for common errors
   - Include specific remediation steps where possible

## 7. Implementation Guidelines

### 7.1 Synchronous Approach

For a single-user application, use a synchronous implementation for simplicity:

```python
def connect_to_invokeai(url):
    """Connect to InvokeAI server."""
    try:
        response = requests.get(f"{url}/api/v1/app/version", timeout=10)
        if response.status_code == 200:
            return True
        return False
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return False

def get_batch_status(url, batch_id):
    """Get status of a generation batch."""
    try:
        response = requests.get(f"{url}/api/v1/queue/default/b/{batch_id}/status", timeout=10)
        if response.status_code == 200:
            return response.json()
        return {"error": f"API error: {response.status_code}"}
    except Exception as e:
        logger.error(f"Error checking batch status: {e}")
        return {"error": str(e)}
```

### 7.2 Template-Based Graph Construction

Create a function to build the graph structure:

```python
def build_generation_graph(params):
    """Build generation graph from parameters."""
    # Create node IDs
    node_ids = {
        "model_loader": f"sdxl_model_loader:{uuid.uuid4().hex[:8]}",
        "pos_prompt": f"sdxl_compel_prompt:{uuid.uuid4().hex[:8]}",
        # ... other node IDs
    }
    
    # Build graph structure
    graph = {
        "prepend": False,
        "batch": {
            "graph": {
                "id": f"sdxl_graph:{uuid.uuid4().hex[:8]}",
                "nodes": { ... },
                "edges": [ ... ]
            },
            "runs": 1,
            "data": [ ... ],
            "origin": "photo_gallery",
            "destination": "gallery"
        }
    }
    
    return graph
```

### 7.3 Direct Retrieval Implementation

Implement direct retrieval in the generation service:

```python
def process_completed_batch(batch_id, session_id, step_id):
    """Process a completed generation batch."""
    # Get batch status
    status = get_batch_status(batch_id)
    
    # Extract image names
    image_names = []
    for item in status.get("items", []):
        if item.get("status") == "completed" and "result" in item:
            image_names.append(item["result"].get("image_name"))
    
    # Create photo records with pending status
    photo_ids = []
    for image_name in image_names:
        photo = create_photo_record(
            image_name=image_name,
            session_id=session_id,
            step_id=step_id,
            retrieval_status="pending"
        )
        photo_ids.append(photo.id)
    
    # Start retrieval for each photo
    for photo_id in photo_ids:
        retrieve_photo(photo_id)
    
    return photo_ids

def retrieve_photo(photo_id):
    """Retrieve a photo from InvokeAI."""
    # Get photo record
    photo = get_photo(photo_id)
    
    try:
        # Generate storage paths
        storage_path = generate_storage_path(photo)
        thumbnail_path = generate_thumbnail_path(photo)
        
        # Retrieve image, thumbnail, and metadata
        response = get_image(photo.invoke_id)
        thumbnail = get_thumbnail(photo.invoke_id)
        metadata = get_metadata(photo.invoke_id)
        
        # Save files
        save_file(storage_path, response)
        save_file(thumbnail_path, thumbnail)
        
        # Update photo record
        update_photo_retrieval_status(
            photo_id=photo_id,
            status="completed",
            storage_path=storage_path,
            thumbnail_path=thumbnail_path,
            metadata=metadata
        )
        
        return True
        
    except Exception as e:
        # Log error and update photo record
        logger.error(f"Error retrieving photo {photo_id}: {e}")
        update_photo_retrieval_status(
            photo_id=photo_id,
            status="failed",
            error=str(e)
        )
        
        return False
```

### 7.4 Background Tasks

Implement a simple task scheduler for periodic operations:

```python
def setup_background_tasks():
    """Setup background tasks for the application."""
    scheduler = BackgroundScheduler()
    
    # Retry failed retrievals every minute
    scheduler.add_job(
        retry_failed_retrievals,
        'interval',
        minutes=1,
        id='retry_retrievals'
    )
    
    # Refresh model cache daily
    scheduler.add_job(
        refresh_model_cache,
        'interval',
        days=1,
        id='refresh_models'
    )
    
    # Check idle pods every 5 minutes
    scheduler.add_job(
        check_idle_pods,
        'interval',
        minutes=5,
        id='check_idle'
    )
    
    scheduler.start()
    return scheduler
```

## 8. Remote Pod Management (RunPod)

### 8.1 Pod Lifecycle

1. **Starting a Pod**:
   - Use RunPod API to start a pod with InvokeAI image
   - Store pod ID and start time in application_settings
   - Generate base URL using pod ID
   - Update backend mode to 'remote'

2. **Monitoring Activity**:
   - Update last_connected_at timestamp with each API call
   - Calculate idle time based on this timestamp
   - Compare against idle_timeout_minutes setting

3. **Automatic Shutdown**:
   - Check idle time periodically
   - If idle time exceeds threshold, stop pod
   - Record session duration and cost
   - Switch to local mode

### 8.2 Cost Tracking

1. **Session Cost Calculation**:
   - Track session start time
   - Calculate duration in hours at shutdown
   - Multiply by hourly rate for pod type
   - Update current_session_cost in settings

2. **Lifetime Statistics**:
   - Maintain lifetime_usage_hours counter
   - Maintain lifetime_cost counter
   - Update both at session end

### 8.3 Error Recovery

1. **Connection Loss**:
   - Detect failed connections to pod
   - Attempt reconnection with exponential backoff
   - If pod crashed, offer restart option

2. **Pod Start Failure**:
   - Detect failures during pod start
   - Provide specific error information to user
   - Maintain local mode as fallback

## 9. Example API Requests and Responses

### 9.1 Model Listing

Request:
```
GET /api/v2/models/
```

Response:
```json
{
  "models": [
    {
      "key": "8b1b897c-d66d-410a-b7a9-55fd5546c55e",
      "hash": "blake3:a238b0fa133bc4f3136aaa8d47de33a668a18380602e7f1d1dca01e286fe2d64",
      "name": "SDXL 1.0",
      "base": "sdxl",
      "type": "main",
      "description": "Stable Diffusion XL base model",
      "format": "diffusers",
      "default_settings": {
        "vae": "00dd6f256eac35494a42b199d952c35b4b25b202a12d9f8c4fc46e9cdbad2ced",
        "scheduler": "euler",
        "steps": 30,
        "cfg_scale": 7.5,
        "width": 1024,
        "height": 1024
      }
    },
    {
      "key": "00dd6f25-eac3-5494-a42b-199d952c35b4",
      "hash": "blake3:00dd6f256eac35494a42b199d952c35b4b25b202a12d9f8c4fc46e9cdbad2ced",
      "name": "SDXL VAE",
      "base": "sdxl",
      "type": "vae"
    }
  ]
}
```

### 9.2 Batch Status

Request:
```
GET /api/v1/queue/default/b/4610a34c-7120-448e-a4f3-cb88f87dbdf4/status
```

Response:
```json
{
  "queue_id": "default",
  "batch_id": "4610a34c-7120-448e-a4f3-cb88f87dbdf4",
  "origin": "photo_gallery",
  "destination": "gallery",
  "pending": 0,
  "in_progress": 0,
  "completed": 2,
  "failed": 0,
  "canceled": 0,
  "total": 2,
  "items": [
    {
      "item_id": 42,
      "batch_id": "4610a34c-7120-448e-a4f3-cb88f87dbdf4",
      "status": "completed",
      "completed_at": "2025-02-25T22:25:10.123Z",
      "result": {
        "image_name": "a1b2c3d4-5678-90e1-f2g3-h4i5j6k7l8m9"
      }
    },
    {
      "item_id": 43,
      "batch_id": "4610a34c-7120-448e-a4f3-cb88f87dbdf4",
      "status": "completed",
      "completed_at": "2025-02-25T22:25:15.789Z",
      "result": {
        "image_name": "b2c3d4e5-6789-01f2-g3h4-i5j6k7l8m9n0"
      }
    }
  ]
}
```

### 9.3 Image Metadata

Request:
```
GET /api/v1/images/i/a1b2c3d4-5678-90e1-f2g3-h4i5j6k7l8m9/metadata
```

Response:
```json
{
  "image_name": "a1b2c3d4-5678-90e1-f2g3-h4i5j6k7l8m9",
  "width": 1024,
  "height": 1024,
  "created_at": "2025-02-25T22:25:10.123Z",
  "updated_at": "2025-02-25T22:25:10.123Z",
  "is_intermediate": false,
  "metadata": {
    "generation_mode": "sdxl_txt2img",
    "positive_prompt": "Beautiful mountain landscape with trees [CID:abc123]",
    "negative_prompt": "blurry, low quality",
    "model": {
      "key": "8b1b897c-d66d-410a-b7a9-55fd5546c55e",
      "hash": "blake3:a238b0fa133bc4f3136aaa8d47de33a668a18380602e7f1d1dca01e286fe2d64",
      "name": "SDXL 1.0",
      "type": "main"
    },
    "vae": {
      "key": "00dd6f25-eac3-5494-a42b-199d952c35b4",
      "hash": "blake3:00dd6f256eac35494a42b199d952c35b4b25b202a12d9f8c4fc46e9cdbad2ced",
      "name": "SDXL VAE",
      "type": "vae"
    },
    "steps": 30,
    "cfg_scale": 7.5,
    "scheduler": "euler",
    "seed": 123456,
    "width": 1024,
    "height": 1024
  }
}
```

## 10. Implementation Checklist

- [ ] Basic InvokeAI connection management
- [ ] Model listing and caching
- [ ] VAE compatibility detection
- [ ] Graph construction for generation
- [ ] Batch submission and monitoring
- [ ] Photo record creation for generation results
- [ ] Direct image retrieval and storage
- [ ] Error handling and categorization
- [ ] Retry mechanism for failed retrievals
- [ ] Background task management
- [ ] RunPod integration (if using remote mode)
- [ ] Cost tracking and reporting
- [ ] Idle detection and auto-shutdown