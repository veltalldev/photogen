# Photo Gallery Backend

A self-hosted, single-user photo gallery API with integrated AI image generation capabilities via InvokeAI.

## Overview

This backend provides a REST API for:
- Photo management (upload, retrieval, organization)
- Album creation and management
- AI image generation workflows using InvokeAI integration
- Sharing capabilities via secure links

The application is designed for simplicity and personal use, focusing on providing an intuitive API for browsing photos and generating variations using InvokeAI.

## Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Local InvokeAI installation (optional for development with mocks)
- RunPod API key (optional, for remote InvokeAI integration)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/photo-gallery.git
   cd photo-gallery/backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create development database:
   ```bash
   createdb photo_gallery_dev
   ```

5. Create test database:
   ```bash
   createdb photo_gallery_test
   ```

## Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Update the `.env` file with your configuration values:
   ```
   # Database
   DATABASE_URL=postgresql://postgres:postgres@localhost/photo_gallery_dev
   TEST_DATABASE_URL=postgresql://postgres:postgres@localhost/photo_gallery_test

   # InvokeAI
   INVOKEAI_LOCAL_URL=http://localhost:9090
   INVOKEAI_CONNECTION_TIMEOUT=10
   INVOKEAI_READ_TIMEOUT=30

   # RunPod (optional)
   RUNPOD_API_KEY=your_api_key_here
   RUNPOD_POD_TYPE=NVIDIA A5000
   RUNPOD_IDLE_TIMEOUT=30

   # Application
   MAX_UPLOAD_SIZE=20971520  # 20MB
   MAX_BATCH_SIZE=10
   RETRIEVAL_MAX_ATTEMPTS=5
   ```

## Database Setup

1. Initialize the database schema:
   ```bash
   alembic upgrade head
   ```

## Running the Server

1. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

2. API will be available at: http://127.0.0.1:8000/api/v1

## Testing

1. Run all tests:
   ```bash
   pytest
   ```

2. Run specific test modules:
   ```bash
   pytest tests/unit/test_photos.py
   pytest tests/integration/
   ```

3. Run with coverage:
   ```bash
   pytest --cov=app tests/
   ```

## Project Structure

```
backend/
├── app/                  # Main application package
│   ├── api/              # API routes and handlers
│   ├── database/         # Database connection and utilities
│   ├── models/           # SQLAlchemy models
│   ├── services/         # Business logic services
│   ├── utils/            # Utility functions and helpers
│   ├── config/           # Configuration management
│   └── main.py           # Application entry point
│
├── alembic/              # Database migrations
│   └── versions/         # Migration versions
│
├── data/                 # Data storage
│   └── photos/           # Photo storage
│       ├── generated/    # AI-generated images
│       ├── uploaded/     # User uploads
│       └── thumbnails/   # Image thumbnails
│
├── tests/                # Test files
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
│
├── alembic.ini           # Alembic configuration
├── pytest.ini            # Pytest configuration
└── requirements.txt      # Dependencies
```

## Core Components

### Models

The data models include:
- `Photo`: Core image entity with metadata and retrieval status
- `Album`: Collection of photos with metadata
- `GenerationSession`: Workflow for AI-generated images
- `GenerationStep`: Individual generation step with alternatives

### Services

Key services include:
- `PhotoService`: Photo management and retrieval
- `AlbumService`: Album and collection management
- `GenerationService`: InvokeAI integration and generation workflow
- `InvokeAIClient`: Communication with InvokeAI API
- `ModelService`: AI model management

### API Endpoints

The REST API includes endpoints for:
- `/api/v1/photos`: Photo management
- `/api/v1/albums`: Album management
- `/api/v1/generation`: AI generation workflows
- `/api/v1/models`: AI model management
- `/api/v1/settings`: Application settings
- `/api/v1/share`: Sharing functionality

## Documentation

Additional documentation can be found in the `docs/` directory:
- Technical specifications
- Implementation guides
- Database schema
- API contracts

## Development Guidelines

1. Follow the implementation guide in `docs/dev/`
2. Write tests for all new functionality
3. Run the test suite before submitting changes
4. Keep the API consistent with the API contract spec
5. Maintain database schema documentation when making changes

## Common Pitfalls

See `docs/pitfalls.md` for guidance on:
- Authentication & Authorization simplicity
- Resource management constraints
- AI generation interface boundaries
- Performance considerations