# Simplified Database Schema for Photo Gallery

This document outlines the simplified database schema for the Photo Gallery application, focusing on reducing complexity while maintaining all required functionality for a single-user application.

## Key Simplifications

1. **Synchronous Database Operations**: Replaced async database operations with synchronous equivalents.

2. **Reduced Table Count**: 
   - Merged model compatibility information into the models table
   - Removed the dedicated retrieval queue
   - Removed cost tracking as a separate table
   - Moved standardized generation presets into application settings

3. **Direct Retrieval Tracking**: Added retrieval fields directly to the photos table instead of using a separate queue system.

4. **Combined Model Information**: Consolidated model and VAE information into a single table.

5. **Simplified Settings**: Used a combination of direct fields and JSONB for application settings.

## Database Schema

### Photos Table
```sql
CREATE TABLE photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL UNIQUE,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Generation metadata
    is_generated BOOLEAN DEFAULT FALSE,
    generation_prompt TEXT,
    generation_negative_prompt TEXT,
    generation_params JSONB,
    source_image_id UUID REFERENCES photos(id),
    
    -- InvokeAI specific fields
    invoke_id TEXT,            -- Image name from InvokeAI
    model_key TEXT,            -- UUID key of the model used
    
    -- System metadata
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- File paths
    local_storage_path TEXT,
    local_thumbnail_path TEXT,
    
    -- Retrieval tracking (simplified)
    retrieval_status TEXT DEFAULT 'completed',
    retrieval_attempts INTEGER DEFAULT 0,
    last_retrieval_attempt TIMESTAMP WITH TIME ZONE,
    retrieval_error TEXT
);

-- Index for retrieval status to quickly find pending/failed retrievals
CREATE INDEX idx_photos_retrieval_status ON photos (retrieval_status) 
    WHERE retrieval_status != 'completed';

-- Index for deleted photos to exclude from queries
CREATE INDEX idx_photos_deleted_at ON photos (deleted_at) 
    WHERE deleted_at IS NOT NULL;

-- Index for efficient lookup by InvokeAI ID
CREATE INDEX idx_photos_invoke_id ON photos (invoke_id)
    WHERE invoke_id IS NOT NULL;

-- Index for text search on generation prompt
CREATE INDEX idx_photos_generation_prompt ON photos USING gin(to_tsvector('english', generation_prompt));
```

### Albums Table
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

### Shared Links Table
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

### Generation Workflow Tables
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

CREATE TABLE generation_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES generation_sessions(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES generation_steps(id),
    prompt TEXT NOT NULL,
    negative_prompt TEXT,
    parameters JSONB NOT NULL,
    
    -- InvokeAI specific fields
    model_key TEXT NOT NULL,        -- UUID key of the model
    batch_id TEXT NOT NULL,         -- ID of the batch from InvokeAI
    correlation_id TEXT,            -- Optional ID for correlating images
    
    selected_image_id UUID REFERENCES photos(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    position INTEGER,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    
    -- Tracking fields
    batch_size INTEGER DEFAULT 1,
    images_retrieved INTEGER DEFAULT 0,
    images_pending INTEGER DEFAULT 0,
    images_failed INTEGER DEFAULT 0
);

-- Index for efficient session step retrieval
CREATE INDEX idx_generation_steps_session ON generation_steps(session_id, position);

-- Index for tree traversal
CREATE INDEX idx_generation_steps_parent ON generation_steps(parent_id);

-- Index for step status monitoring
CREATE INDEX idx_generation_steps_status ON generation_steps(status)
    WHERE status IN ('pending', 'processing');

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

### Models Table (Simplified)
```sql
CREATE TABLE models (
    key TEXT PRIMARY KEY,            -- UUID key from InvokeAI
    name TEXT NOT NULL,              -- Display name
    type TEXT NOT NULL,              -- main, vae, etc.
    base TEXT NOT NULL,              -- sd15, sdxl, etc.
    hash TEXT NOT NULL,              -- Blake3 hash required by InvokeAI
    description TEXT,
    
    -- Default parameters specific to this model
    default_width INTEGER,
    default_height INTEGER,
    default_steps INTEGER,
    default_cfg_scale NUMERIC(5, 2),
    default_scheduler TEXT,
    
    -- VAE information (combined from model_compatibility)
    default_vae_key TEXT,
    default_vae_hash TEXT,
    
    cached_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for model type
CREATE INDEX idx_models_type ON models(type);

-- Index for model base
CREATE INDEX idx_models_base ON models(base);
```

### Prompt Templates Table
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

### Application Settings Table
```sql
CREATE TABLE application_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1), -- Singleton table
    
    -- Generation defaults (standardized presets)
    aspect_ratios JSONB DEFAULT '[
        {"name": "Square (1:1)", "width": 1024, "height": 1024},
        {"name": "Portrait (2:3)", "width": 832, "height": 1216},
        {"name": "Landscape (3:2)", "width": 1216, "height": 832}
    ]'::jsonb,
    
    -- Default parameters that apply to all models
    default_steps INTEGER NOT NULL DEFAULT 30,
    default_cfg_scale NUMERIC(4, 2) NOT NULL DEFAULT 7.5,
    default_scheduler TEXT NOT NULL DEFAULT 'euler',
    default_batch_size INTEGER NOT NULL DEFAULT 4,
    
    -- Backend settings
    backend_mode TEXT NOT NULL DEFAULT 'local' CHECK (backend_mode IN ('local', 'remote')),
    local_backend_url TEXT NOT NULL DEFAULT 'http://localhost:9090',
    remote_backend_url TEXT,
    runpod_api_key TEXT,
    runpod_pod_type TEXT DEFAULT 'NVIDIA A5000',
    idle_timeout_minutes INTEGER DEFAULT 30,
    
    -- RunPod cost tracking (simplified)
    current_session_start TIMESTAMP WITH TIME ZONE,
    current_session_cost NUMERIC(10, 4) DEFAULT 0,
    
    -- Settings JSON for extensibility
    settings_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Implementation Guidelines

1. **Use Synchronous Database Operations**:
   ```python
   # Example repository method
   def get_photo(self, id: UUID) -> Optional[Photo]:
       return self.session.query(Photo).filter(Photo.id == id).first()
   ```

2. **Handle Retrieval Directly**:
   ```python
   # Example retrieval handling
   def retrieve_generated_image(self, invoke_id: str, photo_id: UUID) -> bool:
       try:
           # Retrieve image from InvokeAI
           image_data = self.invokeai_client.get_image(invoke_id)
           metadata = self.invokeai_client.get_metadata(invoke_id)
           
           # Save to file system
           save_path = self._save_image_to_disk(image_data, invoke_id)
           
           # Update photo record
           photo = self.session.query(Photo).filter(Photo.id == photo_id).first()
           if photo:
               photo.local_storage_path = save_path
               photo.retrieval_status = 'completed'
               self.session.commit()
               return True
               
           return False
       except Exception as e:
           # Update retrieval attempt info
           photo = self.session.query(Photo).filter(Photo.id == photo_id).first()
           if photo:
               photo.retrieval_attempts += 1
               photo.last_retrieval_attempt = datetime.now()
               photo.retrieval_status = 'failed'
               photo.retrieval_error = str(e)
               self.session.commit()
               
           return False
   ```

3. **Simplified Cost Tracking**:
   ```python
   # Example cost tracking update
   def update_session_cost(self, elapsed_minutes: float, hourly_rate: float) -> None:
       settings = self.session.query(ApplicationSettings).first()
       if not settings:
           return
           
       # Calculate cost
       hours_elapsed = elapsed_minutes / 60
       cost_increment = hours_elapsed * hourly_rate
       
       # Update settings
       settings.current_session_cost += cost_increment
       self.session.commit()
   ```

4. **Aspect Ratio Management**:
   ```python
   # Example method to get available aspect ratios
   def get_aspect_ratios(self) -> List[Dict]:
       settings = self.session.query(ApplicationSettings).first()
       if not settings:
           return []
           
       return settings.aspect_ratios
   ```

## Note on SQLAlchemy Models

The SQLAlchemy models should be updated to reflect these schema changes. For example:

```python
class Photo(Base):
    __tablename__ = 'photos'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False, unique=True)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    
    # Generation metadata
    is_generated = Column(Boolean, default=False)
    generation_prompt = Column(Text)
    generation_negative_prompt = Column(Text)
    generation_params = Column(JSONB)
    source_image_id = Column(UUID(as_uuid=True), ForeignKey('photos.id'))
    
    # InvokeAI specific fields
    invoke_id = Column(String)
    model_key = Column(String)
    
    # System metadata
    last_accessed_at = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))
    
    # File paths
    local_storage_path = Column(String)
    local_thumbnail_path = Column(String)
    
    # Retrieval tracking
    retrieval_status = Column(String, default='completed')
    retrieval_attempts = Column(Integer, default=0)
    last_retrieval_attempt = Column(DateTime(timezone=True))
    retrieval_error = Column(Text)
    
    # Relationships
    source_photo = relationship('Photo', remote_side=[id], backref='derived_photos')
    album_associations = relationship('AlbumPhoto', back_populates='photo', cascade='all, delete-orphan')
    step_alternatives = relationship('StepAlternative', back_populates='photo', cascade='all, delete-orphan')
```