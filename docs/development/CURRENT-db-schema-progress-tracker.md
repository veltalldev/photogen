# Database Schema Implementation Progress Tracker

## 2.1. Create SQLAlchemy models for core tables
- [ ] 2.1.1. Photos table
  - [ ] 2.1.1.1. Define basic fields (id, filename, dimensions, file_size, mime_type)
  - [ ] 2.1.1.2. Add generation-related fields (is_generated, generation_prompt, etc)
  - [ ] 2.1.1.3. Add InvokeAI metadata fields (invoke_id, model_key, etc)
  - [ ] 2.1.1.4. Add system metadata fields (timestamps, deleted_at)
  - [ ] 2.1.1.5. Add retrieval tracking fields (status, attempts, paths)
  - [ ] 2.1.1.6. Define indexes for efficient lookups
  - [ ] 2.1.1.7. Add relationships to related tables
  - [ ] 2.1.1.8. Add SQLAlchemy methods/properties

- [ ] 2.1.2. Albums table
  - [ ] 2.1.2.1. Define basic fields (id, name, description)
  - [ ] 2.1.2.2. Add timestamps (created_at, updated_at)
  - [ ] 2.1.2.3. Add cover_photo_id with relationship
  - [ ] 2.1.2.4. Define indexes for lookups
  - [ ] 2.1.2.5. Add SQLAlchemy methods/properties

- [ ] 2.1.3. Album_Photos relationship table
  - [ ] 2.1.3.1. Define composite primary key (album_id, photo_id)
  - [ ] 2.1.3.2. Add added_at timestamp
  - [ ] 2.1.3.3. Add position field for ordering
  - [ ] 2.1.3.4. Define foreign key relationships
  - [ ] 2.1.3.5. Create index for efficient album content retrieval

- [ ] 2.1.4. Shared_Links table
  - [ ] 2.1.4.1. Define primary key and basic fields
  - [ ] 2.1.4.2. Add access_key field with unique constraint
  - [ ] 2.1.4.3. Add sharing target fields (photo_id OR album_id)
  - [ ] 2.1.4.4. Add expiration and timestamp fields
  - [ ] 2.1.4.5. Create constraint for sharing target check
  - [ ] 2.1.4.6. Define indexes for access_key lookups
  - [ ] 2.1.4.7. Add index for expired links cleanup
  - [ ] 2.1.4.8. Add SQLAlchemy relationships

## 2.2. Create models for generation workflow tables
- [ ] 2.2.1. Generation_Sessions table
  - [ ] 2.2.1.1. Define primary key and timestamps
  - [ ] 2.2.1.2. Add entry_type field with valid values
  - [ ] 2.2.1.3. Add source_image_id with relationship
  - [ ] 2.2.1.4. Add status field with valid values
  - [ ] 2.2.1.5. Add statistics fields (steps, images generated)
  - [ ] 2.2.1.6. Add index for active sessions
  - [ ] 2.2.1.7. Add SQLAlchemy relationships to steps

- [ ] 2.2.2. Generation_Steps table
  - [ ] 2.2.2.1. Define primary key and foreign keys
  - [ ] 2.2.2.2. Add prompt and negative_prompt fields
  - [ ] 2.2.2.3. Add parameters JSONB field
  - [ ] 2.2.2.4. Add InvokeAI specific fields (model_key, batch_id, etc)
  - [ ] 2.2.2.5. Add status field with valid values
  - [ ] 2.2.2.6. Add position and timestamps
  - [ ] 2.2.2.7. Add retrieval tracking fields
  - [ ] 2.2.2.8. Create indexes for session relationships
  - [ ] 2.2.2.9. Create index for parent relationship (tree structure)
  - [ ] 2.2.2.10. Add index for status monitoring
  - [ ] 2.2.2.11. Add index for batch_id lookup
  - [ ] 2.2.2.12. Create index for correlation_id

- [ ] 2.2.3. Step_Alternatives table
  - [ ] 2.2.3.1. Define composite primary key (step_id, image_id)
  - [ ] 2.2.3.2. Add selected boolean field with default
  - [ ] 2.2.3.3. Add created_at timestamp
  - [ ] 2.2.3.4. Create index for finding alternatives by step
  - [ ] 2.2.3.5. Create index for selected alternatives

## 2.3. Create models for InvokeAI integration tables
- [ ] 2.3.1. Model_Cache table
  - [ ] 2.3.1.1. Define key as primary key (UUID from InvokeAI)
  - [ ] 2.3.1.2. Add hash field (Blake3 hash)
  - [ ] 2.3.1.3. Add name, type, and base fields
  - [ ] 2.3.1.4. Add description field
  - [ ] 2.3.1.5. Add default parameter fields
  - [ ] 2.3.1.6. Add cached_at timestamp
  - [ ] 2.3.1.7. Create index for model type
  - [ ] 2.3.1.8. Create index for model base

- [ ] 2.3.2. Model_Compatibility table
  - [ ] 2.3.2.1. Define composite primary key (model_key, vae_key)
  - [ ] 2.3.2.2. Add is_default boolean field
  - [ ] 2.3.2.3. Add created_at timestamp
  - [ ] 2.3.2.4. Create index for finding compatible VAEs
  - [ ] 2.3.2.5. Create index for default VAEs

- [ ] 2.3.3. Retrieval_Queue table
  - [ ] 2.3.3.1. Define primary key and foreign keys
  - [ ] 2.3.3.2. Add backend_url and invoke_id fields
  - [ ] 2.3.3.3. Add batch_id and correlation_id fields
  - [ ] 2.3.3.4. Add retry tracking fields (attempts, timestamps)
  - [ ] 2.3.3.5. Add status field with valid values
  - [ ] 2.3.3.6. Add error_message field
  - [ ] 2.3.3.7. Add priority field for queue ordering
  - [ ] 2.3.3.8. Create unique constraint for photo_id
  - [ ] 2.3.3.9. Create index for retrieval scheduling
  - [ ] 2.3.3.10. Create index for batch monitoring

- [ ] 2.3.4. Backend_Configuration table
  - [ ] 2.3.4.1. Create singleton table with id=1 check
  - [ ] 2.3.4.2. Add mode field with valid values
  - [ ] 2.3.4.3. Add URL fields for local and remote backends
  - [ ] 2.3.4.4. Add remote pod configuration fields
  - [ ] 2.3.4.5. Add idle timeout setting
  - [ ] 2.3.4.6. Add updated_at timestamp
  - [ ] 2.3.4.7. Add connection status fields

- [ ] 2.3.5. Cost_Tracking table (for remote mode)
  - [ ] 2.3.5.1. Define primary key and pod_id field
  - [ ] 2.3.5.2. Add session time fields (start, end)
  - [ ] 2.3.5.3. Add duration and cost fields
  - [ ] 2.3.5.4. Add created_at timestamp
  - [ ] 2.3.5.5. Create index for pod_id lookups

## 2.4. Create models for template and preferences tables
- [ ] 2.4.1. Prompt_Templates table
  - [ ] 2.4.1.1. Define primary key and basic fields
  - [ ] 2.4.1.2. Add prompt_text and negative_prompt fields
  - [ ] 2.4.1.3. Add category and is_favorite fields
  - [ ] 2.4.1.4. Add timestamps (created_at, updated_at)
  - [ ] 2.4.1.5. Create index for favorites
  - [ ] 2.4.1.6. Create index for categories

- [ ] 2.4.2. Generation_Presets table
  - [ ] 2.4.2.1. Define primary key and name fields
  - [ ] 2.4.2.2. Add model and VAE reference fields
  - [ ] 2.4.2.3. Add parameter fields (width, height, steps, etc)
  - [ ] 2.4.2.4. Add is_default boolean field
  - [ ] 2.4.2.5. Add timestamps
  - [ ] 2.4.2.6. Create index for default preset

- [ ] 2.4.3. Application_Settings table
  - [ ] 2.4.3.1. Create singleton table with id=1 check
  - [ ] 2.4.3.2. Add generation default fields
  - [ ] 2.4.3.3. Add backend setting fields
  - [ ] 2.4.3.4. Add retrieval setting fields
  - [ ] 2.4.3.5. Add settings_json field for extensibility
  - [ ] 2.4.3.6. Add updated_at timestamp

## 2.5. Set up Alembic for migrations
- [ ] 2.5.1. Initialize Alembic
  - [ ] 2.5.1.1. Run alembic init command
  - [ ] 2.5.1.2. Configure alembic.ini file
  - [ ] 2.5.1.3. Setup env.py with SQLAlchemy connection
  - [ ] 2.5.1.4. Configure version locations

- [ ] 2.5.2. Create initial migration
  - [ ] 2.5.2.1. Generate initial migration script
  - [ ] 2.5.2.2. Review and adjust migration script
  - [ ] 2.5.2.3. Add comments for clarity
  - [ ] 2.5.2.4. Add downgrade logic

- [ ] 2.5.3. Implement migration execution workflow
  - [ ] 2.5.3.1. Create migration runner script
  - [ ] 2.5.3.2. Add database verification step
  - [ ] 2.5.3.3. Test upgrade and downgrade operations
  - [ ] 2.5.3.4. Document migration process

## 2.6. Define database schema relationships
- [ ] 2.6.1. Document table relationships
  - [ ] 2.6.1.1. Create relationship diagram
  - [ ] 2.6.1.2. Document one-to-many relationships
  - [ ] 2.6.1.3. Document many-to-many relationships
  - [ ] 2.6.1.4. Document foreign key constraints

- [ ] 2.6.2. Add database comments
  - [ ] 2.6.2.1. Add comments to tables
  - [ ] 2.6.2.2. Add comments to columns
  - [ ] 2.6.2.3. Document constraints and indexes

## 2.7. Test database schema
- [ ] 2.7.1. Create schema validation tests
  - [ ] 2.7.1.1. Test table creation
  - [ ] 2.7.1.2. Test constraints
  - [ ] 2.7.1.3. Test indexes
  - [ ] 2.7.1.4. Test relationships

- [ ] 2.7.2. Create sample data insertion tests
  - [ ] 2.7.2.1. Create test data for each table
  - [ ] 2.7.2.2. Test insertion workflows
  - [ ] 2.7.2.3. Test relationship integrity
  - [ ] 2.7.2.4. Test cascading behaviors