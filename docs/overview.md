# Photo Gallery Project Overview & Documentation Guide

## Project Definition

A self-hosted, single-user photo gallery application with integrated AI image generation capabilities. The application serves as both a portfolio project and a practical tool for personal use, focusing on providing an intuitive interface for browsing photos and generating variations using InvokeAI.

## Core Characteristics

### Application Type
- Single-user application
- Self-hosted
- Web-based interface
- Local integration with InvokeAI

### Key Constraints
- Must be simple enough for portfolio demonstration
- Focused on personal use case
- Tightly coupled with local InvokeAI server
- Limited to single-user architecture with sharing capabilities

## Primary Use Cases

### Photo Management
1. Browse photo gallery
2. View full-resolution images
3. Organize and manage photos
4. Share photos via secure URLs

### AI Generation Workflow
1. Select base image for inspiration
2. Craft and refine prompts interactively
3. Preview generated variations
4. Compare variations with base image
5. Select and save desired outputs
6. Clean up undesired generations

## Required Specification Documents

### 1. System Architecture Specification
Current status: Initial version exists, needs revision
Required updates:
- Simplify user management schema
- Remove multi-user complexities
- Add prompt management system
- Update sharing mechanism for single-user context

### 2. Frontend Specification
Status: Needs creation
Key sections:
- UI component architecture
- Interactive prompt crafting interface
- Image comparison system
- Gallery management interface
- State management strategy

### 3. Backend API Specification
Status: Needs creation
Key sections:
- RESTful endpoint definitions
- File management system
- InvokeAI integration details
- Error handling patterns

### 4. Database Schema
Status: Needs revision
Simplified schema needed for:
- Photo metadata
- Generation history
- Sharing links
- Templates/favorites
Remove:
- User management complexity
- Multi-user access controls
- Complex permission systems

### 5. Storage Architecture
Status: Needs creation
Key sections:
- File organization strategy
- Thumbnail management
- Temporary vs permanent storage
- Cleanup procedures

### 6. Integration Contract
Status: Exists, needs review
Key sections:
- InvokeAI API interaction
- Error handling
- Response processing
- File system conventions

## Documentation Priorities

1. **First Priority**
   - Revised system architecture
   - Simplified database schema
   - Core API specification

2. **Second Priority**
   - Frontend component specification
   - Storage architecture
   - UI/UX workflow documentation

3. **Third Priority**
   - Deployment guide
   - Development setup
   - Testing strategy

## Required Updates to Existing Specs

### System Architecture Document
- Remove multi-user complexities
- Simplify access control to focus on sharing
- Add prompt management system
- Update file organization strategy

### Database Schema
Current tables to simplify:
```sql
-- Remove:
- user_preferences
- user management complexity

-- Simplify:
CREATE TABLE photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type TEXT NOT NULL,
    thumbnail_path TEXT,
    
    -- Generation metadata
    is_generated BOOLEAN DEFAULT FALSE,
    generation_prompt TEXT,
    generation_params JSONB,
    source_image_id UUID REFERENCES photos(id),
    
    -- System metadata
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE albums (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    cover_photo_id UUID REFERENCES photos(id)
);

CREATE TABLE album_photos (
    album_id UUID REFERENCES albums(id),
    photo_id UUID REFERENCES photos(id),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    position INTEGER,
    PRIMARY KEY (album_id, photo_id)
);

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

-- New tables needed:
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    prompt TEXT NOT NULL,
    negative_prompt TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE generation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_photo_id UUID REFERENCES photos(id),
    result_photo_id UUID REFERENCES photos(id),
    prompt TEXT NOT NULL,
    negative_prompt TEXT,
    parameters JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Next Steps

1. Review and validate this understanding
2. Prioritize specification development
3. Begin detailed specification creation
4. Review and iterate on specifications