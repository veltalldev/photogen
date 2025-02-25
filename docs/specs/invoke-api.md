# Updated InvokeAI Integration Contract Specification

## 1. Overview

This specification defines the integration contract between the Photo Gallery application and InvokeAI instances (both local and remote), focusing solely on API interactions without any file system dependencies.

## 2. Connection Management

### 2.1 Backend URL Formation

**Local Mode**: 
- Base URL: `http://localhost:9090`
- No authentication required

**Remote Mode**:
- Base URL: `https://{pod-id}-9090.proxy.runpod.net` 
- No authentication required for API access
- RunPod API key required for pod management (separate from InvokeAI access)

### 2.2 Connection Testing

**Health Check Endpoint**:
- `GET /api/v1/app/version`
- Expected response: Version information
- Used to validate connectivity

## 3. API Integration Points

### 3.1 Core InvokeAI Endpoints

**Model Management**:
- `GET /api/v2/models/` - List available models

**Generation Queue**:
- `POST /api/v1/queue/{queue_id}/enqueue_batch` - Queue new generation requests
- `GET /api/v1/queue/{queue_id}/status` - Get queue status
- `GET /api/v1/queue/{queue_id}/b/{batch_id}/status` - Get batch status

**Image Retrieval**:
- `GET /api/v1/images/i/{image_name}/metadata` - Retrieve image metadata
- `GET /api/v1/images/i/{image_name}/full` - Retrieve full-resolution image
- `GET /api/v1/images/i/{image_name}/thumbnail` - Retrieve image thumbnail

**Image Management**:
- `DELETE /api/v1/images/i/{image_name}` - Delete image (for cleanup)

### 3.2 Generation Parameters

**Core Parameters**:
```typescript
interface GenerationParameters {
    // Base Configuration
    model: string;              // Model to use for generation
    
    // Image Parameters
    width: number;             // From source image or user setting
    height: number;            // From source image or user setting
    steps: number;             // Configurable, default: 30
    cfg_scale: number;         // Configurable, default: 7.5
    scheduler: string;         // Configurable, default: "euler"
    
    // Generation Control
    prompt: string;            // Required
    negative_prompt?: string;  // Optional
    seed?: number;            // Optional, random if not specified
    batch_size: number;       // 1-10 images per request
}
```

## 4. Image Retrieval Process

### 4.1 Process Flow

1. **Queue Generation**:
   - Prepare generation request
   - Submit via `POST /api/v1/queue/default/enqueue_batch`
   - Receive batch ID

2. **Monitor Status**:
   - Poll `GET /api/v1/queue/default/b/{batch_id}/status`
   - Continue until status is "completed" or "failed"

3. **Retrieve Results**:
   - For each image in results:
     - Get metadata: `GET /api/v1/images/i/{image_id}/metadata`
     - Get full image: `GET /api/v1/images/i/{image_id}/full`
     - Get thumbnail: `GET /api/v1/images/i/{image_id}/thumbnail`

4. **Store Locally**:
   - Save images in appropriate directory structure
   - Create database records with local paths
   - Update retrieval status

### 4.2 Error Handling

1. **Connection Errors**:
   - Implement exponential backoff (1s, 2s, 4s, 8s, etc.)
   - Retry up to 5 times for immediate failures
   - For persistent failures, schedule delayed retry

2. **Generation Errors**:
   - Parse error response from API
   - Categorize error (resource issue, parameter issue, etc.)
   - Provide appropriate UI feedback

3. **Retrieval Errors**:
   - Track partially retrieved images
   - Retry failed retrievals independently
   - Allow manual retry via UI

## 5. Request/Response Contracts

### 5.1 Batch Generation Request

**Request Format**:
```json
{
    "prepend": false,
    "batch": {
        "graph": {
            "id": "sdxl_graph:test1",
            "nodes": {...},
            "edges": [...]
        },
        "runs": 1,
        "data": [
            [
                {"node_path": "noise:1", "field_name": "seed", "items": [987654, 123456]}
            ]
        ]
    },
    "origin": "photo_gallery",
    "destination": "gallery"
}
```

**Response Format**:
```json
{
    "batch_id": "string",
    "queue_id": "string",
    "success": true,
    "queued_items": [
        {
            "item_id": "string",
            "batch_id": "string",
            "status": "string",
            "priority": 0
        }
    ]
}
```

### 5.2 Batch Status

**Request**: `GET /api/v1/queue/{queue_id}/b/{batch_id}/status`

**Response Format**:
```json
{
    "batch_id": "string",
    "queue_id": "string",
    "items": [
        {
            "item_id": "string",
            "batch_id": "string",
            "status": "string",
            "completed_at": "string",
            "started_at": "string",
            "created_at": "string",
            "result": {
                "image_name": "string"
            }
        }
    ],
    "pending_count": 0,
    "in_progress_count": 0,
    "completed_count": 0,
    "failed_count": 0
}
```

### 5.3 Image Metadata

**Request**: `GET /api/v1/images/i/{image_name}/metadata`

**Response Format**:
```json
{
    "image_name": "string",
    "width": 0,
    "height": 0,
    "created_at": "string",
    "updated_at": "string",
    "is_intermediate": false,
    "session_id": "string",
    "workflow": {},
    "metadata": {}
}
```

## 6. Graph Structure for Generation

### 6.1 Core Nodes Required

1. **Model Loader**:
   - Type: `sdxl_model_loader`
   - Loads the diffusion model

2. **Prompt Processors**:
   - Type: `sdxl_compel_prompt`
   - One for positive prompt, one for negative

3. **Collectors**:
   - Type: `collect`
   - Aggregate conditioning

4. **Noise Generator**:
   - Type: `noise`
   - Creates initial noise

5. **Latent Denoiser**:
   - Type: `denoise_latents`
   - Core generation process

6. **VAE Loader**:
   - Type: `vae_loader`
   - Loads VAE model

7. **Metadata**:
   - Type: `core_metadata`
   - Records generation parameters

8. **Output Processor**:
   - Type: `l2i` (latents to image)
   - Converts latents to final image

### 6.2 Example Graph Structure

```json
{
  "id": "sdxl_graph:test1",
  "nodes": {
    "sdxl_model_loader:1": {
      "type": "sdxl_model_loader",
      "id": "sdxl_model_loader:1",
      "model": {
        "key": "model_key",
        "name": "model_name",
        "base": "sdxl",
        "type": "main"
      },
      "is_intermediate": true,
      "use_cache": true
    },
    // Additional nodes omitted for brevity
  },
  "edges": [
    // Connections between nodes omitted for brevity
  ]
}
```

## 7. Implementation Guidelines

### 7.1 Connection Management

1. **URL Formation**:
   - Local: `http://localhost:9090`
   - Remote: `https://{pod-id}-9090.proxy.runpod.net`

2. **Health Checks**:
   - Perform before major operations
   - Use version endpoint for minimal overhead

3. **Timeout Configuration**:
   - Connection timeout: 10 seconds
   - Read timeout: 30 seconds
   - Generation status polling: 5 seconds

### 7.2 Image Retrieval

1. **Efficient Retrieval**:
   - Parallel retrieval where possible
   - Sequential fallback for stability
   - Prioritize metadata before images

2. **Storage Organization**:
   - Store by session and step ID
   - Maintain original filenames with UUIDs
   - Create appropriate directory structure

3. **Cleanup Process**:
   - Delete rejected alternatives if requested
   - Maintain selected images and alternatives
   - Clean up after session completion

### 7.3 Error Recovery

1. **Immediate Retries**:
   - Use exponential backoff
   - Limit to 5 attempts
   - Provide user feedback during retry

2. **Persistent Failures**:
   - Log detailed error information
   - Schedule background retry
   - Offer manual retry option
   - Allow session to continue where possible

3. **Resource Issues**:
   - Detect GPU memory errors
   - Offer reduced batch size
   - Suggest parameter adjustments