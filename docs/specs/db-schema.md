# Updated Database Schema

This document defines the updated database schema for the Photo Gallery application, incorporating the generation workflow and remote retrieval capabilities.

## Core Tables

### Photos
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

-- Index for retrieval status to quickly find pending/failed retrievals
CREATE INDEX idx_photos_retrieval_status ON photos (retrieval_status) 
    WHERE retrieval_status != 'completed';

-- Index for deleted photos to exclude from queries
CREATE INDEX idx_photos_deleted_at ON photos (deleted_at) 
    WHERE deleted_at IS NOT NULL;
```

### Albums
```sql
CREATE TABLE albums (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    cover_photo_id UUID REFERENCES photos(id)
);

CREATE TABLE album_photos (
    album_id UUID REFERENCES albums(id) ON DELETE CASCADE,
    photo_id UUID REFERENCES photos(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    position INTEGER,
    PRIMARY KEY (album_id, photo_id)
);

-- Index for efficient album content retrieval
CREATE INDEX idx_album_photos_position ON album_photos(album_id, position);
```

### Sharing
```sql
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

-- Index for access key lookups
CREATE INDEX idx_shared_links_access_key ON shared_links(access_key);

-- Index for expired links cleanup
CREATE INDEX idx_shared_links_expires_at ON shared_links(expires_at)
    WHERE expires_at IS NOT NULL;
```

## Generation Workflow Tables

### Generation Sessions
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

-- Index for active sessions
CREATE INDEX idx_generation_sessions_status ON generation_sessions(status);
```

### Generation Steps
```sql
CREATE TABLE generation_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES generation_sessions(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES generation_steps(id) ON DELETE SET NULL,
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

-- Index for efficient session step retrieval
CREATE INDEX idx_generation_steps_session ON generation_steps(session_id, position);

-- Index for tree traversal
CREATE INDEX idx_generation_steps_parent ON generation_steps(parent_id);

-- Index for step status monitoring
CREATE INDEX idx_generation_steps_status ON generation_steps(status)
    WHERE status IN ('pending', 'processing');
```

### Step Alternatives
```sql
CREATE TABLE step_alternatives (
    step_id UUID NOT NULL REFERENCES generation_steps(id) ON DELETE CASCADE,
    image_id UUID NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
    selected BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (step_id, image_id)
);

-- Index for finding all alternatives for a step
CREATE INDEX idx_step_alternatives_step ON step_alternatives(step_id);

-- Index for selected alternatives
CREATE INDEX idx_step_alternatives_selected ON step_alternatives(step_id, selected)
    WHERE selected = TRUE;
```

## Backend Management Tables

### Backend Configuration
```sql
CREATE TABLE backend_configuration (
    id INTEGER PRIMARY KEY CHECK (id = 1), -- Singleton table
    mode TEXT NOT NULL DEFAULT 'local' CHECK (mode IN ('local', 'remote')),
    local_url TEXT NOT NULL DEFAULT 'http://localhost:9090',
    remote_url TEXT,
    remote_pod_id TEXT,
    idle_timeout_minutes INTEGER NOT NULL DEFAULT 30,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Cost Tracking
```sql
CREATE TABLE cost_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pod_id TEXT NOT NULL,
    session_start TIMESTAMP WITH TIME ZONE NOT NULL,
    session_end TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    estimated_cost NUMERIC(10, 4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for pod_id lookups
CREATE INDEX idx_cost_tracking_pod_id ON cost_tracking(pod_id);
```

### Retrieval Queue
```sql
CREATE TABLE retrieval_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    photo_id UUID NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
    backend_url TEXT NOT NULL,
    remote_image_id TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_attempt TIMESTAMP WITH TIME ZONE,
    next_attempt TIMESTAMP WITH TIME ZONE,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (photo_id)
);

-- Index for retrieval scheduling
CREATE INDEX idx_retrieval_queue_next_attempt ON retrieval_queue(next_attempt)
    WHERE status = 'pending';
```

## Templates and Preferences

### Prompt Templates
```sql
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    prompt_text TEXT NOT NULL,
    negative_prompt TEXT,
    category TEXT,
    is_favorite BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for favorites
CREATE INDEX idx_prompt_templates_favorite ON prompt_templates(is_favorite)
    WHERE is_favorite = TRUE;

-- Index for categories
CREATE INDEX idx_prompt_templates_category ON prompt_templates(category);
```

### Model Favorites
```sql
CREATE TABLE model_favorites (
    model_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    notes TEXT,
    last_used TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Application Settings
```sql
CREATE TABLE application_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1), -- Singleton table
    default_image_width INTEGER NOT NULL DEFAULT 1024,
    default_image_height INTEGER NOT NULL DEFAULT 1024,
    default_steps INTEGER NOT NULL DEFAULT 30,
    default_cfg_scale NUMERIC(4, 2) NOT NULL DEFAULT 7.5,
    default_scheduler TEXT NOT NULL DEFAULT 'euler',
    default_batch_size INTEGER NOT NULL DEFAULT 4,
    runpod_api_key TEXT,
    settings_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Database Comments

```sql
COMMENT ON TABLE photos IS 'Stores metadata for all photos, both uploaded and generated';
COMMENT ON COLUMN photos.retrieval_status IS 'Status of image retrieval from remote backend';
COMMENT ON COLUMN photos.local_storage_path IS 'Path to the locally stored image file';

COMMENT ON TABLE generation_sessions IS 'Represents complete generation workflows';
COMMENT ON COLUMN generation_sessions.entry_type IS 'How the session was started: from scratch or refining an existing image';
COMMENT ON COLUMN generation_sessions.status IS 'Current status of the generation session';

COMMENT ON TABLE generation_steps IS 'Individual steps within a generation session';
COMMENT ON COLUMN generation_steps.parent_id IS 'Previous step in the linear history, null for initial step';
COMMENT ON COLUMN generation_steps.position IS 'Order within the session for display purposes';

COMMENT ON TABLE step_alternatives IS 'Generated image alternatives for each step';
COMMENT ON COLUMN step_alternatives.selected IS 'Whether this is the chosen alternative that continues the timeline';

COMMENT ON TABLE backend_configuration IS 'Singleton table for backend connection settings';
COMMENT ON COLUMN backend_configuration.idle_timeout_minutes IS 'Minutes of inactivity before automatically stopping remote pod';

COMMENT ON TABLE retrieval_queue IS 'Queue for background image retrieval processing';
COMMENT ON COLUMN retrieval_queue.next_attempt IS 'When to next attempt retrieval for failed or pending items';
```

## Schema Migration Approach

When implementing this schema, follow these migration guidelines:

1. **First Phase**: Core table updates
   - Add new columns to `photos` table
   - Create indices for retrieval status

2. **Second Phase**: Generation workflow tables
   - Create session, step, and alternative tables
   - Establish relationships with photos table

3. **Third Phase**: Backend management
   - Create configuration and cost tracking tables
   - Implement retrieval queue

4. **Final Phase**: Templates and preferences
   - Create remaining tables for user experience
   - Add any missing indices
   
Each phase should include comprehensive testing to ensure data integrity and query performance.