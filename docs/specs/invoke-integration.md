# Updated InvokeAI Integration Contract Specification

## 1. Overview

This specification defines the integration contract between the Photo Gallery application and InvokeAI instances (both local and remote). It has been updated based on extensive testing to ensure accurate and reliable integration with the InvokeAI API.

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

Implement continuous status monitoring with these patterns:

1. **Connection Status**:
   - Cache connection status to minimize API calls
   - Refresh status before critical operations
   - Track response times for early warning of performance issues

2. **Pod Status** (Remote Mode):
   - Monitor pod state using RunPod API
   - Track uptime and cost metrics
   - Implement auto-shutdown logic for inactive pods

3. **Resource Monitoring**:
   - Adapt generation requests based on backend status
   - Adjust batch sizes during high-load periods
   - Implement queuing for multiple generation requests

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

**Model Selection Strategy**:
1. Cache model information after initial query
2. Filter by `"type": "main"` for base models
3. Match models with compatible VAEs based on `"base"` field
4. Use both `key` and `hash` in generation requests
5. Periodically refresh model cache to detect new models

### 3.2 Generation Queue

**Submitting Generation Request**:
- `POST /api/v1/queue/{queue_id}/enqueue_batch` - Queue a new generation batch
- Use `default` for queue_id in most cases
- Request must include complete graph structure (see Section 5)
- **Critical**: Include both model key and hash in request

**Batch Status Monitoring**:
- `GET /api/v1/queue/{queue_id}/status` - Overall queue status
- `GET /api/v1/queue/{queue_id}/b/{batch_id}/status` - Specific batch status
- Implement exponential backoff for polling (starting at 2s)
- Watch for status changes to catch completion or errors

### 3.3 Image Retrieval

**Listing Recent Images**:
- `GET /api/v1/images/?limit={n}` - Get most recent n images
- Use this after batch completion to retrieve generated images
- Filter by timestamp to match batch completion time

**Retrieving Image Content**:
- `GET /api/v1/images/i/{image_name}/metadata` - Image metadata
- `GET /api/v1/images/i/{image_name}/full` - Full-resolution image
- `GET /api/v1/images/i/{image_name}/thumbnail` - Image thumbnail

**Image Cleanup** (optional):
- `DELETE /api/v1/images/i/{image_name}` - Delete image from InvokeAI storage
- Consider cleanup strategy to avoid storage issues on InvokeAI side

## 4. Image Retrieval Process

### 4.1 Complete Retrieval Workflow

After submitting a generation request and receiving confirmation of completion, follow this process:

1. **List Recent Images**:
   - Request exactly as many images as were in the generation batch
   - Use the `/api/v1/images/?limit={batch_size}` endpoint
   - Sort by creation time (newest first)

2. **Verify Images Match Batch**:
   - Compare image creation timestamps with batch completion time
   - Alternatively, use unique identifiers in prompts for verification
   - Be prepared to handle cases where images don't match expected count

3. **Retrieve and Store Images**:
   - For each image, in parallel (with rate limiting):
     - Download full image 
     - Download thumbnail
     - Retrieve metadata
   - Store all assets according to your file organization strategy
   - Update database with retrieval status and local paths

4. **Handle Metadata**:
   - Extract generation parameters from metadata 
   - Store parameters for later reference
   - Pay special attention to seed values for reproducibility

### 4.2 Batch-to-Image Correlation Strategy

**Challenge**: The InvokeAI API doesn't directly link batch IDs to resulting image names

**Solution**: Implement these strategies:

1. **Timestamp-Based Correlation**:
   - Record the exact time when the batch completes
   - Retrieve images created within a narrow time window
   - Order by creation time (newest first) and take the first `batch_size` images

2. **Prompt-Based Verification**:
   - Include a unique identifier in each prompt (e.g., a UUID)
   - Verify this identifier in the metadata of retrieved images
   - This provides strong correlation even in multi-user environments

3. **Sequential Approach**:
   - Process one batch at a time in single-user mode
   - Complete full retrieval before starting next generation
   - Simplifies correlation at the cost of concurrency

### 4.3 Error Handling and Recovery

Implement robust error handling:

1. **Connection Failures**:
   - Implement exponential backoff for transient failures
   - Maximum retry count: 5 for immediate operations
   - For persistent failures, schedule delayed retry

2. **Partial Retrievals**:
   - Track individual image retrieval status 
   - Allow for partial success (some images retrieved, others failed)
   - Implement independent retry for failed retrievals

3. **Recovery Process**:
   - Store batch and image information in local database
   - Implement background job for retry of failed retrievals
   - Provide user feedback on retrieval status

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

**Critical Finding**: To ensure complete metadata in the output image:

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

### 5.5 Complete Example Graph

```json
{
  "prepend": false,
  "batch": {
    "graph": {
      "id": "sdxl_graph:test1",
      "nodes": {
        "sdxl_model_loader:1": {
          "type": "sdxl_model_loader",
          "id": "sdxl_model_loader:1",
          "model": {
            "key": "ece5fa0b-5d3d-4bc4-9912-5caf6d270f53",
            "name": "kokioIllu_v20",
            "base": "sdxl",
            "type": "main",
            "hash": "blake3:3b49eb5f584e69ad7a09b535ad163a60ed0c912159fac5434d3fdc2a0a88b7ef"
          },
          "is_intermediate": true,
          "use_cache": true
        },
        "sdxl_compel_prompt:1": {
          "type": "sdxl_compel_prompt",
          "id": "sdxl_compel_prompt:1",
          "prompt": "Mountain landscape with lake and trees",
          "style": "Mountain landscape with lake and trees",
          "is_intermediate": true,
          "use_cache": true
        },
        "collect:1": {
          "type": "collect",
          "id": "collect:1",
          "is_intermediate": true,
          "use_cache": true
        },
        "sdxl_compel_prompt:2": {
          "type": "sdxl_compel_prompt",
          "id": "sdxl_compel_prompt:2",
          "prompt": "blurry, low quality",
          "style": "",
          "is_intermediate": true,
          "use_cache": true
        },
        "collect:2": {
          "type": "collect",
          "id": "collect:2",
          "is_intermediate": true,
          "use_cache": true
        },
        "noise:1": {
          "type": "noise",
          "id": "noise:1",
          "seed": 123456,
          "width": 1024,
          "height": 1024,
          "use_cpu": true,
          "is_intermediate": true,
          "use_cache": true
        },
        "denoise_latents:1": {
          "type": "denoise_latents",
          "id": "denoise_latents:1",
          "cfg_scale": 7.5,
          "cfg_rescale_multiplier": 0,
          "scheduler": "euler",
          "steps": 30,
          "denoising_start": 0,
          "denoising_end": 1,
          "is_intermediate": true,
          "use_cache": true
        },
        "vae_loader:1": {
          "type": "vae_loader",
          "id": "vae_loader:1",
          "vae_model": {
            "key": "c2079afa-3fa5-477c-b10b-1be1e509933e",
            "name": "sdxl-vae-fp16-fix",
            "base": "sdxl",
            "type": "vae",
            "hash": "blake3:9b7c3120af571e8d93fa82d50ef3b5f15727507d0edaae822424951937a008a3"
          },
          "is_intermediate": true,
          "use_cache": true
        },
        "core_metadata:1": {
          "id": "core_metadata:1",
          "type": "core_metadata",
          "is_intermediate": true,
          "use_cache": true,
          "generation_mode": "sdxl_txt2img",
          "cfg_scale": 7.5,
          "cfg_rescale_multiplier": 0,
          "width": 1024,
          "height": 1024,
          "negative_prompt": "blurry, low quality",
          "model": {
            "key": "ece5fa0b-5d3d-4bc4-9912-5caf6d270f53",
            "name": "kokioIllu_v20",
            "base": "sdxl",
            "type": "main",
            "hash": "blake3:3b49eb5f584e69ad7a09b535ad163a60ed0c912159fac5434d3fdc2a0a88b7ef"
          },
          "steps": 30,
          "rand_device": "cpu",
          "scheduler": "euler",
          "vae": {
            "key": "c2079afa-3fa5-477c-b10b-1be1e509933e",
            "name": "sdxl-vae-fp16-fix",
            "base": "sdxl",
            "type": "vae",
            "hash": "blake3:9b7c3120af571e8d93fa82d50ef3b5f15727507d0edaae822424951937a008a3"
          }
        },
        "l2i:1": {
          "type": "l2i",
          "id": "l2i:1",
          "fp32": false,
          "is_intermediate": false,
          "use_cache": false
        }
      },
      "edges": [
        {"source": {"node_id": "sdxl_model_loader:1", "field": "unet"},
         "destination": {"node_id": "denoise_latents:1", "field": "unet"}},
        {"source": {"node_id": "sdxl_model_loader:1", "field": "clip"},
         "destination": {"node_id": "sdxl_compel_prompt:1", "field": "clip"}},
        {"source": {"node_id": "sdxl_model_loader:1", "field": "clip"},
         "destination": {"node_id": "sdxl_compel_prompt:2", "field": "clip"}},
        {"source": {"node_id": "sdxl_model_loader:1", "field": "clip2"},
         "destination": {"node_id": "sdxl_compel_prompt:1", "field": "clip2"}},
        {"source": {"node_id": "sdxl_model_loader:1", "field": "clip2"},
         "destination": {"node_id": "sdxl_compel_prompt:2", "field": "clip2"}},
        {"source": {"node_id": "sdxl_compel_prompt:1", "field": "conditioning"},
         "destination": {"node_id": "collect:1", "field": "item"}},
        {"source": {"node_id": "sdxl_compel_prompt:2", "field": "conditioning"},
         "destination": {"node_id": "collect:2", "field": "item"}},
        {"source": {"node_id": "collect:1", "field": "collection"},
         "destination": {"node_id": "denoise_latents:1", "field": "positive_conditioning"}},
        {"source": {"node_id": "collect:2", "field": "collection"},
         "destination": {"node_id": "denoise_latents:1", "field": "negative_conditioning"}},
        {"source": {"node_id": "noise:1", "field": "noise"},
         "destination": {"node_id": "denoise_latents:1", "field": "noise"}},
        {"source": {"node_id": "denoise_latents:1", "field": "latents"},
         "destination": {"node_id": "l2i:1", "field": "latents"}},
        {"source": {"node_id": "vae_loader:1", "field": "vae"},
         "destination": {"node_id": "l2i:1", "field": "vae"}},
        {"source": {"node_id": "core_metadata:1", "field": "metadata"},
         "destination": {"node_id": "l2i:1", "field": "metadata"}}
      ]
    },
    "runs": 1,
    "data": [
      [
        {"node_path": "noise:1", "field_name": "seed", "items": [123456]},
        {"node_path": "core_metadata:1", "field_name": "seed", "items": [123456]},
        {"node_path": "core_metadata:1", "field_name": "positive_prompt", "items": ["Mountain landscape with lake and trees"]},
        {"node_path": "core_metadata:1", "field_name": "positive_style_prompt", "items": ["Mountain landscape with lake and trees"]}
      ]
    ],
    "origin": "photo_gallery",
    "destination": "gallery"
  }
}
```

## 6. Common Error Patterns and Handling

### 6.1 Network and Connection Errors

1. **Connection Refused**: 
   - Error: `ConnectionRefusedError: [Errno 111] Connection refused`
   - Cause: InvokeAI server not running or incorrect URL
   - Solution: Verify server status, check URL/port

2. **Timeout Errors**:
   - Error: `TimeoutError: Connection timeout`
   - Cause: Server busy, network latency, or resource constraints
   - Solution: Increase timeout value, implement exponential backoff

3. **DNS Resolution Errors** (remote mode):
   - Error: `gaierror: [Errno -2] Name or service not known`
   - Cause: Invalid pod ID or DNS issues
   - Solution: Verify pod ID, check network configuration

### 6.2 API-Related Errors

1. **Invalid Model Key**:
   - Error: `"detail": "Model with key 'invalid_model' not found"`
   - Cause: Model doesn't exist or hash doesn't match
   - Solution: Refresh model list, use exact key and hash from API

2. **Invalid Graph Structure**:
   - Error: `"detail": "Missing required connection for node 'denoise_latents:1'"`
   - Cause: Incomplete or incorrect graph structure
   - Solution: Verify all required edges are present

3. **Parameter Validation Errors**:
   - Error: `"detail": "Value error, cfg_scale must be greater than 1.0"`
   - Cause: Invalid parameter values
   - Solution: Validate parameters against acceptable ranges

4. **Resource Limitations**:
   - Error: `"detail": "CUDA out of memory"`
   - Cause: Insufficient GPU memory
   - Solution: Reduce image dimensions, batch size, or steps

### 6.3 Error Handling Strategy

1. **Categorize Errors**:
   - Network errors: Implement automatic retry with backoff
   - Validation errors: Return specific feedback to user
   - Resource errors: Suggest parameter adjustments
   - Unknown errors: Log details and fall back to defaults

2. **Retry Policy**:
   - Short-term retries: Exponential backoff starting at 2 seconds
   - Long-term retries: Schedule background retry job for persistent failures
   - Maximum attempts: 5 for immediate retries, 3 for scheduled retries

3. **User Feedback**:
   - Provide clear error messages with suggested actions
   - Show progress/status during retry attempts
   - Offer manual retry option for persistent failures

4. **Error Logging**:
   - Log detailed error information including request parameters
   - Track error patterns for identifying systematic issues
   - Include timing information for performance analysis

## 7. Implementation Guidelines

### 7.1 Template-Based Approach

Create a reusable template for generation requests:

1. **Base Template**:
   - Use the graph structure from Section 5.5
   - Replace placeholder values with actual parameters at runtime
   - Generate unique IDs for each request

2. **Template Customization**:
   - Maintain constants for node types and connection patterns
   - Allow for easy customization of generation parameters
   - Support batching through data section modification

### 7.2 Code Structure

```python
class InvokeAIClient:
    def __init__(self, base_url: str = "http://localhost:9090"):
        self.base_url = base_url
        self.model_cache = {}
        self.timeout = httpx.Timeout(connect=10.0, read=30.0, write=10.0)
    
    async def check_connection(self) -> bool:
        """Check if InvokeAI server is accessible"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/v1/app/version")
                return response.status_code == 200
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    async def get_models(self, refresh_cache: bool = False) -> list:
        """Get list of available models, optionally refreshing cache"""
        if self.model_cache and not refresh_cache:
            return self.model_cache
            
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/v2/models/")
                
                if response.status_code == 200:
                    data = response.json()
                    # Filter and organize models
                    main_models = [model for model in data.get("models", []) 
                                  if model.get("type") == "main"]
                    vae_models = [model for model in data.get("models", []) 
                                 if model.get("type") == "vae"]
                    
                    # Create cache structure
                    self.model_cache = {
                        "main": main_models,
                        "vae": vae_models,
                        "timestamp": datetime.now()
                    }
                    return main_models
                else:
                    print(f"Failed to retrieve models: {response.status_code}")
                    return []
        except Exception as e:
            print(f"Error retrieving models: {e}")
            return []
    
    async def generate_images(
        self,
        prompt: str,
        negative_prompt: str = "",
        model_key: str = None,
        vae_key: str = None,
        num_images: int = 1,
        width: int = 1024,
        height: int = 1024,
        steps: int = 30,
        cfg_scale: float = 7.5,
        scheduler: str = "euler",
        random_seed: bool = True
    ) -> dict:
        """Generate images with comprehensive error handling and metadata propagation"""
        # Implementation here using the template approach
        # ...
```

### 7.3 Performance Optimization

1. **Connection Management**:
   - Reuse HTTP client connections when possible
   - Implement connection pooling for high-volume operations
   - Use appropriate timeouts for different operations

2. **Parallel Retrieval**:
   - Process image retrievals in parallel with rate limiting
   - Adjust concurrency based on network conditions
   - Prioritize metadata retrieval before full images

3. **Resource Considerations**:
   - Adjust generation parameters based on model requirements
   - Consider time/quality tradeoffs in steps and dimensions
   - Monitor InvokeAI resource usage for optimal performance

### 7.4 Integration Testing Strategy

1. **Test Connection and Discovery**:
   - Verify connection to both local and remote backends
   - Test model discovery and caching
   - Validate model compatibility detection

2. **Test Generation Flow**:
   - Verify request construction and submission
   - Test batch status monitoring
   - Validate image retrieval and storage

3. **Test Error Scenarios**:
   - Simulate connection failures
   - Test with invalid parameters
   - Verify retry mechanisms

4. **End-to-End Testing**:
   - Verify the complete workflow from start to finish
   - Test with various model and parameter combinations
   - Validate metadata preservation in final images

## 8. Appendix: Response Formats

### 8.1 Batch Status Response

```json
{
  "queue_id": "default",
  "batch_id": "4610a34c-7120-448e-a4f3-cb88f87dbdf4",
  "origin": "photo_gallery",
  "destination": "gallery",
  "pending": 0,
  "in_progress": 0,
  "completed": 1,
  "failed": 0,
  "canceled": 0,
  "total": 1
}
```

### 8.2 Image Metadata Response

```json
{
  "generation_mode": "sdxl_txt2img",
  "positive_prompt": "Mountain landscape with lake and trees",
  "negative_prompt": "blurry, low quality",
  "width": 1024,
  "height": 1024,
  "seed": 123456,
  "rand_device": "cpu",
  "cfg_scale": 7.5,
  "cfg_rescale_multiplier": 0,
  "steps": 30,
  "scheduler": "euler",
  "model": {
    "key": "ece5fa0b-5d3d-4bc4-9912-5caf6d270f53",
    "hash": "blake3:3b49eb5f584e69ad7a09b535ad163a60ed0c912159fac5434d3fdc2a0a88b7ef",
    "name": "kokioIllu_v20",
    "base": "sdxl",
    "type": "main"
  },
  "vae": {
    "key": "c2079afa-3fa5-477c-b10b-1be1e509933e",
    "hash": "blake3:9b7c3120af571e8d93fa82d50ef3b5f15727507d0edaae822424951937a008a3",
    "name": "sdxl-vae-fp16-fix",
    "base": "sdxl",
    "type": "vae"
  },
  "positive_style_prompt": "Mountain landscape with lake and trees",
  "app_version": "3.2.0"
}
```

### 8.3 Images List Response

```json
{
  "limit": 2,
  "offset": 0,
  "total": 336,
  "items": [
    {
      "image_name": "89324353-0a0b-44fd-a995-4bc1bc832a5f.png",
      "image_url": "api/v1/images/i/89324353-0a0b-44fd-a995-4bc1bc832a5f.png/full",
      "thumbnail_url": "api/v1/images/i/89324353-0a0b-44fd-a995-4bc1bc832a5f.png/thumbnail",
      "image_origin": "internal",
      "image_category": "general",
      "width": 1024,
      "height": 1024,
      "created_at": "2025-02-25 23:02:51.337",
      "updated_at": "2025-02-25 23:02:51.337",
      "deleted_at": null,
      "is_intermediate": false,
      "session_id": "c30d49be-3056-4019-8245-aa7ea50ad6ad",
      "node_id": "0afaa910-ba0f-482b-afda-407950057b0a",
      "starred": false,
      "has_workflow": true,
      "board_id": null
    },
    {
      "image_name": "56a79569-3e66-4da5-8bc9-1af34a9524be.png",
      "image_url": "api/v1/images/i/56a79569-3e66-4da5-8bc9-1af34a9524be.png/full",
      "thumbnail_url": "api/v1/images/i/56a79569-3e66-4da5-8bc9-1af34a9524be.png/thumbnail",
      "image_origin": "internal",
      "image_category": "general",
      "width": 1024,
      "height": 1024,
      "created_at": "2025-02-25 23:02:46.722",
      "updated_at": "2025-02-25 23:02:46.722",
      "deleted_at": null,
      "is_intermediate": false,
      "session_id": "0a51413d-3c7c-42ef-96a5-c04bd28971b9",
      "node_id": "4fe513a4-2024-463b-a18a-00144f951575",
      "starred": false,
      "has_workflow": true,
      "board_id": null
    }
  ]
}
```