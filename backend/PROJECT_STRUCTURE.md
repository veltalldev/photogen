# Photo Gallery Project Structure

This document outlines the directory structure of the Photo Gallery application.

## Root Structure

```
photo_gallery/
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
│   │   ├── api/          # API unit tests
│   │   ├── database/     # Database unit tests
│   │   ├── models/       # Models unit tests
│   │   ├── services/     # Services unit tests
│   │   ├── utils/        # Utils unit tests
│   │   └── config/       # Config unit tests
│   │
│   └── integration/      # Integration tests
│       ├── api/          # API integration tests
│       ├── database/     # Database integration tests
│       ├── models/       # Models integration tests
│       └── services/     # Services integration tests
│
├── alembic.ini           # Alembic configuration
├── pytest.ini            # Pytest configuration
├── requirements.txt      # Dependencies
└── run_tests.sh          # Test execution script
```

## App Package Structure

### API Module
Contains route definitions and request handlers for the REST API.

### Database Module
Handles database connections, session management, and retry logic.

### Models Module
Defines SQLAlchemy models representing the database schema.

### Services Module
Implements business logic and core functionality.

### Utils Module
Contains utility functions and helper classes.

### Config Module
Manages application configuration and settings.

## Data Storage Structure

### Photos Directory
Stores all image files with the following organization:

- **generated/** - AI-generated images
  - **sessions/** - Organized by generation session
  - **completed/** - Final selected images

- **uploaded/** - User uploaded images
  - Organized by date (YYYY-MM-DD)

- **thumbnails/** - Image thumbnails
  - Mirrors the structure of generated and uploaded directories