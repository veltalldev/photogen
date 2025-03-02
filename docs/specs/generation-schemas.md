# Updated Database Schema with InvokeAI Integration

This document defines the updated database schema for the Photo Gallery application, incorporating the simplified approach to InvokeAI integration while maintaining all necessary functionality.

## Core Design Principles

1. **Simplicity Over Complexity**: Reduce the number of tables and relationships to improve maintainability.
2. **Direct Tracking**: Track generated image retrieval directly in the photos table rather than with a separate queue.
3. **Synchronous Operations**: Use synchronous database operations for simplicity in a single-user application.
4. **Efficient Queries**: Maintain appropriate indexes for common access patterns.
5. **Extensibility**: Use JSONB fields for flexible extension without schema changes.

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
    generation_negative_prompt TEXT,
    generation_params JSONB,
    source_image_id UUID REFERENCES photos(id),
    
    -- InvokeAI specific fields
    invoke_id TEXT,            -- Image name from InvokeAI
    model_key TEXT,            -- UUID key of the model used
    model_hash TEXT,           -- Blake3 hash of the model used
    model_name TEXT,           -- Display name of the model
    
    -- System metadata
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- File paths
    local_storage_path TEXT,
    local_thumbnail_path TEXT,
    
    -- Simplified retrieval tracking
    retrieval_status TEXT DEFAULT 'completed' 
        CHECK (retrieval_status IN ('pending', 'processing', 'completed', 'failed')),
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

-- Text search index for generation prompt
CREATE INDEX idx_photos_generation_prompt ON photos USING gin(to_tsvector('english', generation_prompt));
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
    
    -- InvokeAI specific fields
    model_key TEXT NOT NULL,        -- UUID key of the model
    model_hash TEXT NOT NULL,       -- Blake3 hash of the model
    model_name TEXT,                -- Display name of the model
    batch_id TEXT NOT NULL,         -- ID of the batch from InvokeAI
    correlation_id TEXT,            -- Optional ID for correlating images
    
    selected_image_id UUID REFERENCES photos(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    position INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,             -- Any error returned from InvokeAI
    
    -- Retrieval tracking fields (simplified)
    batch_size INTEGER DEFAULT 1,   -- Number of images requested
    images_retrieved INTEGER DEFAULT 0,  -- Number of images successfully retrieved
    images_failed INTEGER DEFAULT 0      -- Number of images failed to retrieve
);

-- Index for efficient session step retrieval
CREATE INDEX idx_generation_steps_session ON generation_steps(session_id, position);

-- Index for tree traversal
CREATE INDEX idx_generation_steps_parent ON generation_steps(parent_id);

-- Index for step status monitoring
CREATE INDEX idx_generation_steps_status ON generation_steps(status)
    WHERE status IN ('pending', 'processing');

-- Index for batch ID lookup
CREATE INDEX idx_generation_steps_batch_id ON generation_steps(batch_id);

-- Index for correlation ID lookup
CREATE INDEX idx_generation_steps_correlation_id ON generation_steps(correlation_id)
    WHERE correlation_id IS NOT NULL;
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

## Model Management Tables

### Models Table
```sql
CREATE TABLE models (
    key TEXT PRIMARY KEY,            -- UUID key from InvokeAI
    hash TEXT NOT NULL,              -- Blake3 hash
    name TEXT NOT NULL,              -- Display name
    type TEXT NOT NULL,              -- main, vae, etc.
    base TEXT NOT NULL,              -- sd15, sdxl, etc.
    description TEXT,
    
    -- Default parameters for this model
    default_width INTEGER,
    default_height INTEGER,
    default_steps INTEGER,
    default_cfg_scale NUMERIC(5, 2),
    default_scheduler TEXT,
    
    -- For VAEs, track compatibility
    compatible_with_base TEXT,
    is_default_vae BOOLEAN DEFAULT FALSE,
    
    cached_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- For user management
    is_favorite BOOLEAN DEFAULT FALSE,
    last_used_at TIMESTAMP WITH TIME ZONE
);

-- Index for model type
CREATE INDEX idx_models_type ON models(type);

-- Index for model base
CREATE INDEX idx_models_base ON models(base);

-- Index for compatibility lookups
CREATE INDEX idx_models_compatible_base ON models(compatible_with_base)
    WHERE compatible_with_base IS NOT NULL;

-- Index for favorite models
CREATE INDEX idx_models_favorite ON models(is_favorite)
    WHERE is_favorite = TRUE;
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

### Application Settings
```sql
CREATE TABLE application_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1), -- Singleton table
    
    -- Generation defaults
    aspect_ratios JSONB DEFAULT '[
        {"name": "Square (1:1)", "width": 1024, "height": 1024},
        {"name": "Portrait (2:3)", "width": 832, "height": 1216},
        {"name": "Landscape (3:2)", "width": 1216, "height": 832}
    ]'::jsonb,
    
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
    
    -- Connection status
    is_connected BOOLEAN DEFAULT FALSE,
    last_connected_at TIMESTAMP WITH TIME ZONE,
    api_version TEXT,
    
    -- RunPod session tracking
    current_session_id TEXT,
    current_session_start TIMESTAMP WITH TIME ZONE,
    current_session_cost NUMERIC(10, 4) DEFAULT 0,
    lifetime_usage_hours NUMERIC(10, 2) DEFAULT 0,
    lifetime_cost NUMERIC(10, 2) DEFAULT 0,
    
    -- Retrieval settings
    max_retrieval_attempts INTEGER DEFAULT 5,
    retrieval_retry_delay INTEGER DEFAULT 60, -- seconds
    parallel_retrievals INTEGER DEFAULT 3,
    
    -- Other settings
    settings_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Database Comments

```sql
COMMENT ON TABLE photos IS 'Stores metadata for all photos, both uploaded and generated';
COMMENT ON COLUMN photos.retrieval_status IS 'Status of image retrieval from remote backend';
COMMENT ON COLUMN photos.local_storage_path IS 'Path to the locally stored image file';
COMMENT ON COLUMN photos.invoke_id IS 'Original image name/ID from InvokeAI';
COMMENT ON COLUMN photos.model_key IS 'UUID key of the model used for generation';
COMMENT ON COLUMN photos.model_hash IS 'Blake3 hash of the model used for generation';

COMMENT ON TABLE generation_sessions IS 'Represents complete generation workflows';
COMMENT ON COLUMN generation_sessions.entry_type IS 'How the session was started: from scratch or refining an existing image';
COMMENT ON COLUMN generation_sessions.status IS 'Current status of the generation session';

COMMENT ON TABLE generation_steps IS 'Individual steps within a generation session';
COMMENT ON COLUMN generation_steps.parent_id IS 'Previous step in the linear history, null for initial step';
COMMENT ON COLUMN generation_steps.position IS 'Order within the session for display purposes';
COMMENT ON COLUMN generation_steps.model_key IS 'UUID key of the model used for this step';
COMMENT ON COLUMN generation_steps.model_hash IS 'Blake3 hash of the model used for this step';
COMMENT ON COLUMN generation_steps.batch_id IS 'ID of the batch in InvokeAI';
COMMENT ON COLUMN generation_steps.correlation_id IS 'Optional ID used to correlate images with this step';

COMMENT ON TABLE step_alternatives IS 'Generated image alternatives for each step';
COMMENT ON COLUMN step_alternatives.selected IS 'Whether this is the chosen alternative that continues the timeline';

COMMENT ON TABLE models IS 'Cache of available models from InvokeAI';
COMMENT ON COLUMN models.key IS 'UUID key of the model in InvokeAI';
COMMENT ON COLUMN models.hash IS 'Blake3 hash of the model, required for generation requests';
COMMENT ON COLUMN models.compatible_with_base IS 'For VAEs, which model base they are compatible with';
COMMENT ON COLUMN models.is_default_vae IS 'Whether this VAE is the default for its compatible base';

COMMENT ON TABLE application_settings IS 'Singleton table for application-wide settings';
COMMENT ON COLUMN application_settings.aspect_ratios IS 'Predefined aspect ratios for generation';
COMMENT ON COLUMN application_settings.idle_timeout_minutes IS 'Minutes of inactivity before automatically stopping remote pod';
COMMENT ON COLUMN application_settings.current_session_cost IS 'Estimated cost of current RunPod session';
```

## Implementation Notes

### Synchronous Database Operations

The implementation should use synchronous SQLAlchemy operations for simplicity:

```python
def get_photo_by_id(db_session, photo_id):
    return db_session.query(Photo).filter(Photo.id == photo_id).first()
```

### Direct Retrieval Tracking

Image retrieval status is tracked directly in the photos table, simplifying the retrieval workflow:

```python
def mark_retrieval_pending(db_session, photo_id, invoke_id):
    photo = get_photo_by_id(db_session, photo_id)
    if photo:
        photo.invoke_id = invoke_id
        photo.retrieval_status = 'pending'
        photo.retrieval_attempts = 0
        db_session.commit()
        return True
    return False

def mark_retrieval_complete(db_session, photo_id, local_path, thumbnail_path):
    photo = get_photo_by_id(db_session, photo_id)
    if photo:
        photo.retrieval_status = 'completed'
        photo.local_storage_path = local_path
        photo.local_thumbnail_path = thumbnail_path
        db_session.commit()
        return True
    return False

def mark_retrieval_failed(db_session, photo_id, error_message):
    photo = get_photo_by_id(db_session, photo_id)
    if photo:
        photo.retrieval_attempts += 1
        photo.retrieval_status = 'failed'
        photo.retrieval_error = error_message
        photo.last_retrieval_attempt = datetime.datetime.now()
        db_session.commit()
        return True
    return False
```

### Model Management

The models table now combines model and VAE information for simpler queries:

```python
def get_compatible_vaes(db_session, model_base):
    return db_session.query(Model).filter(
        Model.type == 'vae',
        Model.compatible_with_base == model_base
    ).all()

def get_default_vae(db_session, model_base):
    return db_session.query(Model).filter(
        Model.type == 'vae',
        Model.compatible_with_base == model_base,
        Model.is_default_vae.is_(True)
    ).first()
```

### Application Settings

The application settings table uses both direct fields and a JSONB field for extensibility:

```python
def get_application_settings(db_session):
    settings = db_session.query(ApplicationSettings).first()
    if not settings:
        # Create default settings if not exists
        settings = ApplicationSettings(id=1)
        db_session.add(settings)
        db_session.commit()
    return settings

def update_generation_defaults(db_session, defaults_dict):
    settings = get_application_settings(db_session)
    
    # Update direct fields
    for field in ['default_steps', 'default_cfg_scale', 'default_scheduler', 'default_batch_size']:
        if field in defaults_dict:
            setattr(settings, field, defaults_dict[field])
    
    # Update aspect ratios if provided
    if 'aspect_ratios' in defaults_dict:
        settings.aspect_ratios = defaults_dict['aspect_ratios']
    
    settings.updated_at = datetime.datetime.now()
    db_session.commit()
    return settings
```

### SQLAlchemy Models

Example SQLAlchemy model definitions that match this schema:

```python
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, 
    DateTime, ForeignKey, CheckConstraint, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

class Base:
    # Common base class attributes and methods
    pass

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
    model_hash = Column(String)
    model_name = Column(String)
    
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
    source_image = relationship('Photo', remote_side=[id], backref='derived_images')
    album_photos = relationship('AlbumPhoto', back_populates='photo', cascade='all, delete-orphan')
    step_alternatives = relationship('StepAlternative', back_populates='photo', cascade='all, delete-orphan')
    selected_steps = relationship('GenerationStep', foreign_keys='GenerationStep.selected_image_id',
                                 back_populates='selected_image')
    
    # Constraint for retrieval status
    __table_args__ = (
        CheckConstraint(
            "retrieval_status IN ('pending', 'processing', 'completed', 'failed')",
            name='check_retrieval_status'
        ),
    )

class Album(Base):
    __tablename__ = 'albums'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    cover_photo_id = Column(UUID(as_uuid=True), ForeignKey('photos.id'))
    
    # Relationships
    cover_photo = relationship('Photo', foreign_keys=[cover_photo_id])
    album_photos = relationship('AlbumPhoto', back_populates='album', cascade='all, delete-orphan')

class AlbumPhoto(Base):
    __tablename__ = 'album_photos'
    
    album_id = Column(UUID(as_uuid=True), ForeignKey('albums.id', ondelete='CASCADE'), primary_key=True)
    photo_id = Column(UUID(as_uuid=True), ForeignKey('photos.id', ondelete='CASCADE'), primary_key=True)
    added_at = Column(DateTime(timezone=True), default=datetime.now)
    position = Column(Integer)
    
    # Relationships
    album = relationship('Album', back_populates='album_photos')
    photo = relationship('Photo', back_populates='album_photos')

class SharedLink(Base):
    __tablename__ = 'shared_links'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    photo_id = Column(UUID(as_uuid=True), ForeignKey('photos.id'))
    album_id = Column(UUID(as_uuid=True), ForeignKey('albums.id'))
    access_key = Column(String, nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    last_accessed_at = Column(DateTime(timezone=True))
    
    # Relationships
    photo = relationship('Photo')
    album = relationship('Album')
    
    # Constraint to ensure either photo_id or album_id is set, but not both
    __table_args__ = (
        CheckConstraint(
            "(photo_id IS NOT NULL AND album_id IS NULL) OR (photo_id IS NULL AND album_id IS NOT NULL)",
            name='share_target_check'
        ),
    )

class GenerationSession(Base):
    __tablename__ = 'generation_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    started_at = Column(DateTime(timezone=True), default=datetime.now)
    completed_at = Column(DateTime(timezone=True))
    entry_type = Column(String, nullable=False)
    source_image_id = Column(UUID(as_uuid=True), ForeignKey('photos.id'))
    status = Column(String, nullable=False, default='active')
    
    # Relationships
    source_image = relationship('Photo')
    steps = relationship('GenerationStep', back_populates='session', cascade='all, delete-orphan')
    
    # Constraints
    __table_args__ = (
        CheckConstraint("entry_type IN ('scratch', 'refinement')", name='check_entry_type'),
        CheckConstraint("status IN ('active', 'completed', 'abandoned')", name='check_status'),
    )

class GenerationStep(Base):
    __tablename__ = 'generation_steps'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('generation_sessions.id', ondelete='CASCADE'), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('generation_steps.id', ondelete='SET NULL'))
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text)
    parameters = Column(JSONB, nullable=False)
    
    # InvokeAI specific fields
    model_key = Column(String, nullable=False)
    model_hash = Column(String, nullable=False)
    model_name = Column(String)
    batch_id = Column(String, nullable=False)
    correlation_id = Column(String)
    
    selected_image_id = Column(UUID(as_uuid=True), ForeignKey('photos.id'))
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    completed_at = Column(DateTime(timezone=True))
    position = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default='pending')
    error_message = Column(Text)
    
    # Tracking fields
    batch_size = Column(Integer, default=1)
    images_retrieved = Column(Integer, default=0)
    images_failed = Column(Integer, default=0)
    
    # Relationships
    session = relationship('GenerationSession', back_populates='steps')
    parent = relationship('GenerationStep', remote_side=[id], backref='children')
    selected_image = relationship('Photo', foreign_keys=[selected_image_id])
    alternatives = relationship('StepAlternative', back_populates='step', cascade='all, delete-orphan')
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name='check_step_status'
        ),
    )

class StepAlternative(Base):
    __tablename__ = 'step_alternatives'
    
    step_id = Column(UUID(as_uuid=True), ForeignKey('generation_steps.id', ondelete='CASCADE'), primary_key=True)
    image_id = Column(UUID(as_uuid=True), ForeignKey('photos.id', ondelete='CASCADE'), primary_key=True)
    selected = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    
    # Relationships
    step = relationship('GenerationStep', back_populates='alternatives')
    photo = relationship('Photo', back_populates='step_alternatives')

class Model(Base):
    __tablename__ = 'models'
    
    key = Column(String, primary_key=True)
    hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    base = Column(String, nullable=False)
    description = Column(Text)
    
    # Default parameters
    default_width = Column(Integer)
    default_height = Column(Integer)
    default_steps = Column(Integer)
    default_cfg_scale = Column(Float(precision=5))
    default_scheduler = Column(String)
    
    # For VAEs
    compatible_with_base = Column(String)
    is_default_vae = Column(Boolean, default=False)
    
    cached_at = Column(DateTime(timezone=True), default=datetime.now)
    
    # User preferences
    is_favorite = Column(Boolean, default=False)
    last_used_at = Column(DateTime(timezone=True))

class PromptTemplate(Base):
    __tablename__ = 'prompt_templates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    prompt_text = Column(Text, nullable=False)
    negative_prompt = Column(Text)
    category = Column(String)
    is_favorite = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

class ApplicationSettings(Base):
    __tablename__ = 'application_settings'
    
    id = Column(Integer, primary_key=True, default=1)
    
    # Generation defaults
    aspect_ratios = Column(JSONB)
    default_steps = Column(Integer, nullable=False, default=30)
    default_cfg_scale = Column(Float(precision=4), nullable=False, default=7.5)
    default_scheduler = Column(String, nullable=False, default='euler')
    default_batch_size = Column(Integer, nullable=False, default=4)
    
    # Backend settings
    backend_mode = Column(String, nullable=False, default='local')
    local_backend_url = Column(String, nullable=False, default='http://localhost:9090')
    remote_backend_url = Column(String)
    runpod_api_key = Column(String)
    runpod_pod_type = Column(String, default='NVIDIA A5000')
    idle_timeout_minutes = Column(Integer, default=30)
    
    # Connection status
    is_connected = Column(Boolean, default=False)
    last_connected_at = Column(DateTime(timezone=True))
    api_version = Column(String)
    
    # RunPod session tracking
    current_session_id = Column(String)
    current_session_start = Column(DateTime(timezone=True))
    current_session_cost = Column(Float(precision=10), default=0)
    lifetime_usage_hours = Column(Float(precision=10), default=0)
    lifetime_cost = Column(Float(precision=10), default=0)
    
    # Retrieval settings
    max_retrieval_attempts = Column(Integer, default=5)
    retrieval_retry_delay = Column(Integer, default=60)
    parallel_retrievals = Column(Integer, default=3)
    
    # Other settings
    settings_json = Column(JSONB, nullable=False, default={})
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("id = 1", name='singleton_settings'),
        CheckConstraint("backend_mode IN ('local', 'remote')", name='check_backend_mode'),
    )
```

## Migration Strategy

Since the database will be empty at implementation time, no migration is needed initially. However, for future changes, consider these guidelines:

1. **Incremental Changes**: Make small, focused migrations rather than large restructurings
2. **Data Preservation**: When altering tables, ensure data is preserved through temporary tables if needed
3. **Safe Defaults**: When adding required fields, provide sensible defaults
4. **Testing**: Test migrations on development data before applying to production
5. **Backup**: Always back up the database before migrations

## Implementation Considerations

When implementing this schema, consider these practical aspects:

1. **Repository Layer**:
   - Create separate repository classes for each major entity (Photos, Albums, Models, etc.)
   - Use direct SQLAlchemy queries for efficiency
   - Implement transaction handling for operations that modify multiple tables

2. **Query Optimization**:
   - Use SQLAlchemy query optimization techniques (eager loading, specific column selection)
   - For large collections, implement pagination at the database level
   - Create efficient index-based queries for common operations

3. **Error Handling**:
   - Implement proper error handling for database operations
   - Log database errors with appropriate context
   - Create specific exception types for different database errors

4. **Connection Management**:
   - Create a connection pool for database access
   - Implement session management for request scopes
   - Ensure connections are properly closed even during exceptions

5. **Testing Strategy**:
   - Use an in-memory SQLite database for unit tests
   - Create fixtures for common test data
   - Test database operations with transactions that roll back

## Conclusion

This database schema provides a simplified but comprehensive foundation for the Photo Gallery application with InvokeAI integration. By reducing complexity while maintaining all necessary functionality, it should be easier to implement and maintain while still supporting all required features.