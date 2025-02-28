# Updated API Contract Specification

## 1. Overview

This specification defines the REST API contract for the Photo Gallery application, incorporating detailed integration with InvokeAI for image generation capabilities. This document has been updated to reflect practical findings from InvokeAI integration testing, with particular attention to generation workflows, model management, and image retrieval patterns.

## 2. General Guidelines

### 2.1 Base URL
```
/api/v1/
```

### 2.2 Request/Response Format
- All requests and responses use JSON unless otherwise specified
- Binary data (images) use appropriate content types
- UTF-8 encoding for all text

### 2.3 Pagination
Default pagination parameters for list endpoints:
- `limit`: Default 50, max 100
- `offset`: Default 0
- Response includes total count and pagination metadata

Example response:
```json
{
    "items": [],
    "total": 0,
    "limit": 50,
    "offset": 0
}
```

### 2.4 Error Format
```json
{
    "error": {
        "code": "string",
        "message": "string",
        "details": {}
    }
}
```

Common error codes:
- `not_found`: Resource doesn't exist
- `validation_error`: Invalid input
- `processing_error`: Operation failed
- `storage_error`: File system error
- `network_error`: Remote service communication error
- `invokeai_error`: Error from InvokeAI service
- `resource_error`: Insufficient resources (e.g., GPU memory)
- `model_error`: Model not found or incompatible
- `retrieval_error`: Failed to retrieve generated images

## 3. Core Endpoints

### 3.1 Photos

#### List Photos
```
GET /photos
```

Query Parameters:
- `limit`: Items per page (default: 50)
- `offset`: Pagination offset (default: 0)
- `generated`: Filter by generated status (optional)
- `album_id`: Filter by album (optional)
- `session_id`: Filter by generation session (optional)
- `step_id`: Filter by generation step (optional)
- `since`: Filter by creation date (ISO format, optional)

Response:
```json
{
    "items": [
        {
            "id": "uuid",
            "filename": "string",
            "width": "integer",
            "height": "integer",
            "created_at": "timestamp",
            "is_generated": "boolean",
            "invoke_id": "string?",
            "thumbnail_url": "string",
            "full_url": "string",
            "retrieval_status": "string?",
            "generation_metadata": {
                "prompt": "string?",
                "negative_prompt": "string?",
                "model_id": "string?",
                "model_name": "string?",
                "seed": "integer?",
                "steps": "integer?",
                "cfg_scale": "number?"
            }
        }
    ],
    "total": "integer",
    "limit": "integer",
    "offset": "integer"
}
```

#### Get Photo
```
GET /photos/{id}
```

Response: Binary image data
Content-Type: Original image MIME type
Cache-Control: `public, max-age=31536000`

#### Get Thumbnail
```
GET /photos/thumbnail/{id}
```

Response: Binary image data (WebP)
Content-Type: image/webp
Cache-Control: `public, max-age=31536000`

#### Upload Photo
```
POST /photos
```

Request: Multipart form data
- `file`: Image file

Response:
```json
{
    "id": "uuid",
    "filename": "string",
    "width": "integer",
    "height": "integer",
    "created_at": "timestamp"
}
```

#### Delete Photo
```
DELETE /photos/{id}
```

Response: 204 No Content

#### Retry Photo Retrieval
```
POST /photos/{id}/retry
```

Response:
```json
{
    "id": "uuid",
    "retrieval_status": "string"
}
```

### 3.2 Albums

#### List Albums
```
GET /albums
```

Query Parameters:
- `limit`: Items per page (default: 50)
- `offset`: Pagination offset (default: 0)

Response:
```json
{
    "items": [
        {
            "id": "uuid",
            "name": "string",
            "description": "string?",
            "created_at": "timestamp",
            "updated_at": "timestamp",
            "cover_photo_id": "uuid?",
            "photo_count": "integer"
        }
    ],
    "total": "integer",
    "limit": "integer",
    "offset": "integer"
}
```

#### Create Album
```
POST /albums
```

Request:
```json
{
    "name": "string",
    "description": "string?",
    "cover_photo_id": "uuid?"
}
```

Response: Album object

#### Update Album
```
PATCH /albums/{id}
```

Request:
```json
{
    "name": "string?",
    "description": "string?",
    "cover_photo_id": "uuid?"
}
```

Response: Album object

#### Delete Album
```
DELETE /albums/{id}
```

Response: 204 No Content

#### Album Photos
```
GET /albums/{id}/photos
```

Standard photo list response with album-specific ordering

### 3.3 Sharing

#### Create Share Link
```
POST /share/create
```

Request:
```json
{
    "photo_id": "uuid",
    "expires_at": "timestamp?"
}
```

Response:
```json
{
    "access_key": "string",
    "url": "string",
    "expires_at": "timestamp?"
}
```

#### Get Shared Photo
```
GET /share/{key}
```

Response: Photo object or binary image data based on Accept header

## 4. Generation Workflow Endpoints

### 4.1 Backend Connection Management

#### Get Backend Status
```
GET /backend/status
```

Response:
```json
{
    "mode": "local | remote",
    "url": "string",
    "connected": "boolean",
    "api_version": "string?",
    "pod_id": "string?",
    "pod_status": "string?",
    "last_activity": "timestamp?",
    "uptime": "integer?",
    "current_cost": "number?"
}
```

#### Set Backend Mode
```
POST /backend/mode
```

Request:
```json
{
    "mode": "local | remote"
}
```

Response:
```json
{
    "mode": "local | remote",
    "connected": "boolean",
    "message": "string"
}
```

#### Start Remote Pod
```
POST /backend/pod/start
```

Response:
```json
{
    "pod_id": "string",
    "status": "string",
    "estimated_startup_time": "integer"
}
```

#### Stop Remote Pod
```
POST /backend/pod/stop
```

Response:
```json
{
    "pod_id": "string",
    "status": "string",
    "session_duration": "integer",
    "session_cost": "number"
}
```

### 4.2 Model Management

#### List Available Models
```
GET /models
```

Response:
```json
{
    "items": [
        {
            "id": "string",
            "key": "string",
            "hash": "string",
            "name": "string",
            "type": "string",
            "base": "string",
            "description": "string?",
            "compatible_vae": [
                {
                    "id": "string",
                    "key": "string",
                    "hash": "string",
                    "name": "string"
                }
            ],
            "default_params": {
                "width": "integer",
                "height": "integer",
                "steps": "integer",
                "cfg_scale": "number",
                "scheduler": "string"
            }
        }
    ],
    "last_updated": "timestamp"
}
```

#### Get Model Details
```
GET /models/{key}
```

Response:
```json
{
    "id": "string",
    "key": "string",
    "hash": "string",
    "name": "string",
    "type": "string", 
    "base": "string",
    "description": "string?",
    "compatible_vae": [
        {
            "id": "string",
            "key": "string",
            "hash": "string",
            "name": "string"
        }
    ],
    "default_params": {
        "width": "integer",
        "height": "integer",
        "steps": "integer",
        "cfg_scale": "number",
        "scheduler": "string"
    }
}
```

#### Refresh Model Cache
```
POST /models/refresh
```

Response:
```json
{
    "success": "boolean",
    "models_count": "integer",
    "last_updated": "timestamp"
}
```

### 4.3 Generation Sessions

#### Create Session
```
POST /generation/sessions
```

Request:
```json
{
    "entry_type": "scratch | refinement",
    "source_image_id": "uuid?"
}
```

Response:
```json
{
    "id": "uuid",
    "entry_type": "string",
    "source_image_id": "uuid?",
    "started_at": "timestamp",
    "status": "active"
}
```

#### Get Session
```
GET /generation/sessions/{id}
```

Response:
```json
{
    "id": "uuid",
    "entry_type": "string",
    "source_image_id": "uuid?",
    "started_at": "timestamp",
    "completed_at": "timestamp?",
    "status": "string",
    "steps_count": "integer"
}
```

#### List Sessions
```
GET /generation/sessions
```

Query Parameters:
- `limit`: Items per page (default: 20)
- `offset`: Pagination offset (default: 0)
- `status`: Filter by status (optional)

Response:
```json
{
    "items": [
        {
            "id": "uuid",
            "entry_type": "string",
            "source_image_id": "uuid?",
            "started_at": "timestamp",
            "completed_at": "timestamp?",
            "status": "string",
            "steps_count": "integer",
            "latest_image": {
                "id": "uuid?",
                "thumbnail_url": "string?"
            }
        }
    ],
    "total": "integer",
    "limit": "integer",
    "offset": "integer"
}
```

#### Update Session Status
```
PATCH /generation/sessions/{id}
```

Request:
```json
{
    "status": "completed | abandoned"
}
```

Response:
```json
{
    "id": "uuid",
    "status": "string",
    "completed_at": "timestamp"
}
```

#### Delete Session
```
DELETE /generation/sessions/{id}
```

Response: 204 No Content

### 4.4 Generation Steps

#### Create Step
```
POST /generation/sessions/{session_id}/steps
```

Request:
```json
{
    "prompt": "string",
    "negative_prompt": "string?",
    "parameters": {
        "model_key": "string",
        "model_hash": "string",
        "vae_key": "string?",
        "vae_hash": "string?",
        "width": "integer",
        "height": "integer",
        "steps": "integer",
        "cfg_scale": "number",
        "scheduler": "string",
        "batch_size": "integer",
        "seed": "integer?"
    },
    "parent_id": "uuid?",
    "correlation_id": "string?"
}
```

Response:
```json
{
    "id": "uuid",
    "session_id": "uuid",
    "parent_id": "uuid?",
    "prompt": "string",
    "negative_prompt": "string?",
    "parameters": {},
    "model_key": "string",
    "model_hash": "string",
    "batch_id": "string",
    "correlation_id": "string?",
    "status": "pending",
    "position": "integer",
    "created_at": "timestamp"
}
```

#### Get Step
```
GET /generation/steps/{id}
```

Response:
```json
{
    "id": "uuid",
    "session_id": "uuid",
    "parent_id": "uuid?",
    "prompt": "string",
    "negative_prompt": "string?",
    "parameters": {},
    "model_key": "string",
    "model_hash": "string",
    "batch_id": "string",
    "correlation_id": "string?",
    "selected_image_id": "uuid?",
    "status": "string",
    "position": "integer",
    "created_at": "timestamp"
}
```

#### List Session Steps
```
GET /generation/sessions/{session_id}/steps
```

Response:
```json
{
    "items": [
        {
            "id": "uuid",
            "session_id": "uuid",
            "parent_id": "uuid?",
            "prompt": "string",
            "negative_prompt": "string?",
            "parameters": {},
            "model_key": "string",
            "model_hash": "string",
            "batch_id": "string",
            "correlation_id": "string?",
            "selected_image_id": "uuid?",
            "status": "string",
            "position": "integer",
            "created_at": "timestamp"
        }
    ],
    "total": "integer"
}
```

#### Get Step Status
```
GET /generation/steps/{id}/status
```

Response:
```json
{
    "id": "uuid",
    "status": "pending | processing | completed | failed",
    "batch_id": "string",
    "correlation_id": "string?",
    "progress": "number?",
    "estimated_completion": "timestamp?",
    "error": "string?",
    "retrieval_status": {
        "total": "integer",
        "completed": "integer",
        "pending": "integer",
        "failed": "integer"
    }
}
```

#### Update Step
```
PATCH /generation/steps/{id}
```

Request:
```json
{
    "selected_image_id": "uuid"
}
```

Response:
```json
{
    "id": "uuid",
    "selected_image_id": "uuid",
    "status": "completed"
}
```

### 4.5 Step Alternatives

#### Get Step Alternatives
```
GET /generation/steps/{step_id}/alternatives
```

Response:
```json
{
    "step_id": "uuid",
    "items": [
        {
            "image_id": "uuid",
            "selected": "boolean",
            "created_at": "timestamp",
            "retrieval_status": "completed | pending | failed",
            "photo": {
                "id": "uuid",
                "width": "integer",
                "height": "integer",
                "thumbnail_url": "string",
                "full_url": "string"
            }
        }
    ]
}
```

#### Select Alternative
```
POST /generation/steps/{step_id}/select
```

Request:
```json
{
    "image_id": "uuid"
}
```

Response:
```json
{
    "step_id": "uuid",
    "image_id": "uuid",
    "selected": true,
    "created_at": "timestamp"
}
```

### 4.6 Image Retrieval Management

#### Retry Failed Retrievals
```
POST /generation/steps/{step_id}/retry-retrievals
```

Response:
```json
{
    "step_id": "uuid",
    "batch_id": "string",
    "retrieval_status": {
        "total": "integer",
        "completed": "integer",
        "pending": "integer",
        "failed": "integer",
        "retrying": "integer"
    }
}
```

#### Get Recent Generated Images
```
GET /generation/images
```

Query Parameters:
- `limit`: Maximum images to return (default: 10)  
- `batch_id`: Filter by batch ID (optional)
- `correlation_id`: Filter by correlation ID (optional)
- `since`: Get images generated after timestamp (ISO format)

Response:
```json
{
    "items": [
        {
            "id": "uuid",
            "invoke_id": "string",
            "batch_id": "string?",
            "correlation_id": "string?",
            "width": "integer",
            "height": "integer",
            "created_at": "timestamp",
            "retrieval_status": "string",
            "thumbnail_url": "string",
            "full_url": "string",
            "generation_metadata": {
                "prompt": "string",
                "negative_prompt": "string?",
                "model": {
                    "key": "string",
                    "hash": "string",
                    "name": "string"
                },
                "seed": "integer",
                "steps": "integer",
                "cfg_scale": "number",
                "scheduler": "string"
            }
        }
    ],
    "total": "integer"
}
```

## 5. Caching Strategy

### 5.1 Cache Headers

Static Resources:
- Full images: `public, max-age=31536000`
- Thumbnails: `public, max-age=31536000`

Dynamic Resources:
- Photo lists: `public, max-age=60`
- Album lists: `public, max-age=60`
- Model lists: `public, max-age=300`
- Generation sessions: `no-cache`
- Generation steps: `no-cache`
- Status endpoints: `no-cache`

### 5.2 ETag Support
- Provided for all JSON responses
- Used for photo lists and album contents
- Supports efficient polling

## 6. File Upload

### 6.1 Supported Formats
- JPEG/JPG
- PNG
- WebP
- HEIF/HEIC

### 6.2 Size Limits
- Maximum file size: 20MB
- Maximum dimensions: 8192x8192
- Minimum dimensions: 100x100

### 6.3 Upload Process
1. Client sends multipart form data
2. Server validates format and dimensions
3. Server generates thumbnails
4. Server returns photo metadata

## 7. Batch Operations

### 7.1 Batch Delete
```
POST /photos/batch/delete
```

Request:
```json
{
    "ids": ["uuid", "uuid"]
}
```

Response: 204 No Content

### 7.2 Batch Album Add
```
POST /albums/{id}/photos/batch
```

Request:
```json
{
    "photo_ids": ["uuid", "uuid"]
}
```

Response: 204 No Content

### 7.3 Batch Retrieval Retry
```
POST /photos/batch/retry
```

Request:
```json
{
    "ids": ["uuid", "uuid"]
}
```

Response:
```json
{
    "success_count": "integer",
    "failed_count": "integer",
    "details": {
        "retrying": ["uuid", "uuid"],
        "failed": ["uuid", "uuid"]
    }
}
```

## 8. Error Handling

### 8.1 Network Error Handling
- All endpoints handling remote operations return appropriate error codes
- Transient network errors: 503 Service Unavailable
- Remote service errors: 502 Bad Gateway
- Resource exhaustion errors: 429 Too Many Requests

### 8.2 InvokeAI-Specific Errors

For operations that interact with InvokeAI, these specific error codes are used:

- `invokeai_connection_error`: Cannot connect to InvokeAI backend
- `invokeai_model_error`: Model not found or hash mismatch
- `invokeai_graph_error`: Invalid graph structure
- `invokeai_parameter_error`: Invalid generation parameters
- `invokeai_resource_error`: Resource limitations (e.g., GPU memory)
- `invokeai_unknown_error`: Unspecified InvokeAI error

Example error response:
```json
{
    "error": {
        "code": "invokeai_model_error",
        "message": "Model with key 'abc123' not found or hash does not match",
        "details": {
            "model_key": "abc123",
            "model_hash": "blake3:123...",
            "technical_message": "Original error message from InvokeAI"
        }
    }
}
```

### 8.3 Retry Mechanisms

The API implements a robust retry system for InvokeAI operations:

1. **Automatic Retries**:
   - Status endpoints incorporate exponential backoff
   - Generation requests retry on transient errors
   - Image retrieval implements specific retry logic

2. **Manual Retry Endpoints**:
   - `/photos/{id}/retry` - Retry single image retrieval
   - `/photos/batch/retry` - Retry multiple image retrievals
   - `/generation/steps/{step_id}/retry-retrievals` - Retry all failed retrievals for a step

3. **Retry Status Tracking**:
   - Retrieval status updates in real-time
   - Attempts count tracked and exposed in API
   - Detailed error information preserved for debugging

### 8.4 Status Monitoring

Generation operations provide detailed status endpoints:

1. **Batch Status**:
   - Overall progress tracking
   - Estimated completion time
   - Detailed per-image status

2. **Retrieval Status**:
   - Tracks images pending retrieval
   - Monitors failed retrievals
   - Provides aggregate statistics

3. **Real-time Updates**:
   - Status endpoints support efficient polling
   - Clear progress indicators
   - Detailed error reporting

## 9. InvokeAI Integration Details

### 9.1 Model Information Management

The API maintains a cache of available models from InvokeAI:

1. **Model Cache**:
   - Populated on server startup
   - Refreshed periodically (every 15 minutes)
   - Manual refresh available via API

2. **Model Compatibility**:
   - Tracks compatible VAEs for each model
   - Maps defaults parameters for quick access
   - Provides descriptions and metadata

3. **Model Selection Support**:
   - Filtering by model type and base
   - Default parameter suggestions
   - Popularity tracking (optional)

### 9.2 Correlation Strategies

To address the challenge of correlating InvokeAI-generated images with batches:

1. **Correlation ID**:
   - Optional client-provided ID passed through to InvokeAI
   - Inserted into prompt metadata
   - Used for verification during retrieval

2. **Timestamp-Based Correlation**:
   - Precise tracking of batch completion times
   - Recent image listing with time filters
   - Sorting and filtering by timestamp

3. **Batch Size Tracking**:
   - Exact tracking of expected image count
   - Verification of retrieval completeness
   - Gap detection for missing images

### 9.3 Graph Generation

The API handles the complexity of InvokeAI's graph structure:

1. **Template-Based Approach**:
   - Server maintains graph templates
   - Dynamically populates with request parameters
   - Handles node connections automatically

2. **Parameter Translation**:
   - Simple client parameters translated to graph structure
   - Complex defaults handled by server
   - Parameter validation before submission

3. **Metadata Propagation**:
   - Ensures prompt data is properly set in both nodes and data section
   - Maintains generation history and lineage
   - Preserves complete metadata for retrieved images

## 10. Versioning Strategy

The API follows a simple versioning strategy through the URL path (`/api/v1/`). Future non-backward compatible changes will increment this version number.

### 10.1 Compatibility Guarantees

Current version (v1) guarantees:

1. **Request Format Stability**:
   - No removal of supported fields
   - New optional fields may be added
   - Field types will not change

2. **Response Format Stability**:
   - Existing fields will not be removed
   - New fields may be added
   - Field types will not change

3. **Error Code Stability**:
   - Existing error codes will not change meaning
   - New error codes may be added
   - Error details may be enhanced

### 10.2 Future Versions

Future API versions (v2+) may introduce:

1. **Enhanced Generation Control**:
   - More detailed graph customization
   - Advanced parameter options
   - Alternative generation methods

2. **Additional Retrieval Methods**:
   - Streaming image retrieval
   - Progressive loading enhancements
   - Alternative format support

3. **Workflow Improvements**:
   - Enhanced batch operations
   - Advanced correlation methods
   - Optimized retrieval strategies