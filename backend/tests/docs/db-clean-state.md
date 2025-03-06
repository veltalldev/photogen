# Photo Gallery Database Initial State Specification

## Overview

This document defines the expected initial "clean" state of the database that all testing approaches must achieve, whether using transaction isolation, table truncation, or complete database recreation. This specification serves as the authoritative reference for database verification and ensures consistent test behavior across all testing methodologies.

## Clean State Definition

A database is considered to be in the "clean initial state" when it meets ALL of the following criteria:

### 1. Schema Requirements

- All tables defined in the schema specification exist and have the correct structure
- All constraints (primary keys, foreign keys, checks, unique) are properly defined
- All required extensions are enabled (uuid-ossp)
- All indices are properly created
- No additional tables, views, or other database objects exist beyond those in the schema definition

### 2. Data Requirements

- All application tables contain zero rows
- All sequences are reset to their initial values (typically 1)
- No user-defined functions contain stateful data
- No temporary tables exist

### 3. Database Settings

- Search path is set to public
- Transaction isolation level is set to the default (read committed)
- All database settings match the values defined in the database configuration

## Table Specifications

The following tables constitute the complete database schema and must exist in the clean state:

### Core Tables

1. **photos**
   - Zero rows
   - id sequence reset to 1
   - All foreign key constraints enforced

2. **albums**
   - Zero rows
   - id sequence reset to 1
   - All constraints enforced

3. **album_photos**
   - Zero rows
   - All constraints enforced

4. **shared_links**
   - Zero rows
   - id sequence reset to 1
   - All constraints enforced

### Generation Workflow Tables

1. **generation_sessions**
   - Zero rows
   - id sequence reset to 1
   - All constraints enforced

2. **generation_steps**
   - Zero rows
   - id sequence reset to 1
   - All constraints enforced

3. **step_alternatives**
   - Zero rows
   - All constraints enforced

### Model Management Tables

1. **models**
   - Zero rows
   - All constraints enforced

### Templates and Preferences

1. **prompt_templates**
   - Zero rows
   - id sequence reset to 1
   - All constraints enforced

2. **application_settings**
   - Zero rows
   - All constraints enforced

## Verification Process

To verify the database is in the clean initial state:

1. **Schema Verification**
   - Query information_schema.tables to ensure all expected tables exist
   - Query information_schema.columns to verify column definitions
   - Query information_schema.table_constraints to verify constraints
   - Query pg_indexes to verify all indices exist

2. **Data Verification**
   - Execute COUNT(*) on each table to verify zero rows
   - Query pg_sequences to verify all sequence values are reset

3. **Settings Verification**
   - Query pg_settings to verify database configuration parameters

## Methods to Achieve Clean State

### 1. Transaction Isolation

When using transaction isolation:
- Each test begins a transaction
- All operations are performed within the transaction
- The transaction is rolled back at the end of the test

This approach is efficient but cannot handle schema changes or certain operations that implicitly commit.

### 2. Table Truncation

When using table truncation:
- Disable foreign key constraints (SET CONSTRAINTS ALL DEFERRED)
- Truncate all tables in the correct dependency order
- Reset all sequences
- Re-enable foreign key constraints

This approach handles most testing scenarios but requires careful management of table dependencies.

### 3. Manual Database Recreation

As a last resort:
- Drop the existing database
- Create a new database with the same name
- Enable required extensions
- Apply the schema definition
- Verify the clean state

## Implementation Notes

- The verification process should be automated through a function that can be called at any time
- Verification should produce detailed output when the database is not in the expected clean state
- The clean state verification should be run automatically before each test suite execution

## Conclusion

Adhering to this specification ensures consistent test behavior and reliable results. All testing approaches must achieve exactly this state before test execution begins.