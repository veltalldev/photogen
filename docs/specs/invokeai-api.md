# Updated API Contract Specification

## 1. Overview

This document defines the REST API contract for the Photo Gallery application, incorporating the simplified approach to InvokeAI integration with direct tracking of generated images. The API design prioritizes simplicity and effective patterns for a single-user application.

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
                "model_key": "string?",
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

#### Get Photo Metadata
```
GET /photos/{id}/metadata
```

Response:
```json
{
    "id": "uuid",
    "generation_prompt": "string?",
    "generation_negative_prompt": "string?",
    "generation_params": {
        "model_key": "string?",
        "model_name": "string?",
        "seed": "integer?",
        "steps": "integer?",
        "cfg_scale": "number?",
        "scheduler": "string?", 
        "width": "integer?",
        "height": "integer?"
    },
    "source_image_id": "uuid?",
    "created_at": "timestamp"
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

Query Parameters:
- `limit`: Items per page (default: 50)
- `offset`: Pagination offset (default: 0)

Response: Standard photo list response with album-specific ordering

#### Add Photos to Album
```
POST /albums/{id}/photos
```

Request:
```json
{
    "photo_ids": ["uuid", "uuid"]
}
```

Response: 204 No Content

#### Remove Photos from Album
```
DELETE /albums/{id}/photos
```

Request:
```json
{
    "photo_ids": ["uuid", "uuid"]
}
```

Response: 204 No Content

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
            "key": "string",
            "hash": "string",
            "name": "string",
            "type": "string",
            "base": "string",
            "description": "string?",
            "compatible_vae": [
                {
                    "key": "string",
                    "hash": "string",
                    "name": "string",
                    "is_default": "boolean"
                }
            ],
            "default_params": {
                "width": "integer",
                "height": "integer",
                "steps": "integer",
                "cfg_scale": "number",
                "scheduler": "string"
            },
            "is_favorite": "boolean"
        }
    ],
    "last_updated": "timestamp"
}
```

#### Get Model Details
```
GET /models/{key}
```

Response: Model object (as above)

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

#### Set Model Favorite Status
```
POST /models/{key}/favorite
```

Request:
```json
{
    "is_favorite": "boolean"
}
```

Response:
```json
{
    "key": "string",
    "is_favorite": "boolean"
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

#### Batch Retrieval Retry
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

## 5. Application Settings

### 5.1 Get Settings
```
GET /settings
```

Response:
```json
{
    "generation": {
        "default_steps": "integer",
        "default_cfg_scale": "number",
        "default_scheduler": "string",
        "default_batch_size": "integer",
        "aspect_ratios": [
            {
                "name": "string",
                "width": "integer",
                "height": "integer"
            }
        ]
    },
    "backend": {
        "mode": "local | remote",
        "local_url": "string",
        "remote_url": "string?",
        "idle_timeout_minutes": "integer"
    },
    "retrieval": {
        "max_attempts": "integer",
        "retry_delay": "integer",
        "parallel_retrievals": "integer"
    },
    "cost_tracking": {
        "current_session_cost": "number",
        "lifetime_usage_hours": "number",
        "lifetime_cost": "number"
    }
}
```

### 5.2 Update Settings
```
PATCH /settings
```

Request: Any subset of the settings object  
Response: Updated settings object

## 6. Prompt Templates

### 6.1 List Templates
```
GET /templates
```

Query Parameters:
- `limit`: Items per page (default: 50)
- `offset`: Pagination offset (default: 0)
- `favorite`: Filter favorites (optional)
- `category`: Filter by category (optional)

Response:
```json
{
    "items": [
        {
            "id": "uuid",
            "name": "string",
            "description": "string?",
            "prompt_text": "string",
            "negative_prompt": "string?",
            "category": "string?",
            "is_favorite": "boolean",
            "created_at": "timestamp",
            "updated_at": "timestamp"
        }
    ],
    "total": "integer",
    "limit": "integer",
    "offset": "integer"
}
```

### 6.2 Create Template
```
POST /templates
```

Request:
```json
{
    "name": "string",
    "description": "string?",
    "prompt_text": "string",
    "negative_prompt": "string?",
    "category": "string?",
    "is_favorite": "boolean?"
}
```

Response: Template object

### 6.3 Update Template
```
PATCH /templates/{id}
```

Request: Any subset of template properties  
Response: Updated template object

### 6.4 Delete Template
```
DELETE /templates/{id}
```

Response: 204 No Content

## 7. Error Handling

### 7.1 API Error Responses

All error responses use this format:
```json
{
    "error": {
        "code": "error_code",
        "message": "Human-readable message",
        "details": {
            "parameter": "details about the specific error",
            "technical_error": "original error message (optional)"
        }
    }
}
```

Common error codes:

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `not_found` | 404 | Resource not found |
| `validation_error` | 400 | Invalid input parameters |
| `server_error` | 500 | Unexpected server error |
| `storage_error` | 500 | Error with file storage |
| `invokeai_connection_error` | 502 | Cannot connect to InvokeAI |
| `invokeai_model_error` | 400 | Model not found or hash mismatch |
| `invokeai_graph_error` | 400 | Invalid graph structure |
| `invokeai_generation_error` | 400 | Error during generation |
| `invokeai_retrieval_error` | 502 | Error retrieving generated images |
| `pod_error` | 502 | Error with RunPod operations |

### 7.2 InvokeAI-Specific Errors

Errors from InvokeAI operations include additional details:

```json
{
    "error": {
        "code": "invokeai_generation_error",
        "message": "Failed to generate images",
        "details": {
            "batch_id": "4610a34c-7120-448e-a4f3-cb88f87dbdf4",
            "technical_error": "CUDA out of memory",
            "suggestion": "Try reducing image dimensions or batch size"
        }
    }
}
```

### 7.3 Retrieval Error Handling

For image retrieval errors, the API provides specific information:

```json
{
    "error": {
        "code": "invokeai_retrieval_error",
        "message": "Failed to retrieve some generated images",
        "details": {
            "total": 4,
            "retrieved": 2,
            "failed": 2,
            "batch_id": "4610a34c-7120-448e-a4f3-cb88f87dbdf4",
            "failed_images": [
                {
                    "image_id": "abc123",
                    "error": "Connection timeout"
                }
            ]
        }
    }
}
```

## 8. Versioning

This API follows a simple versioning strategy through the URL path (`/api/v1/`). Future non-backward compatible changes will increment this version number.

### 8.1 Compatibility Guarantees

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