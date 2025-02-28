# PhotoGen

A self-hosted photo gallery application with integrated AI image generation capabilities.

## Overview

PhotoGen is a personal photo management system designed for photographers and digital artists who want to organize their photos and experiment with AI-powered image generation. The application provides an intuitive interface for browsing your photo collection while enabling powerful AI generation workflows using InvokeAI.

### Key Features

- **Photo Management**: Organize, browse, and search your personal photo collection
- **AI Generation**: Create variations of your photos using state-of-the-art image generation models
- **Self-hosted**: Full control over your data with local deployment
- **Single-user Focus**: Streamlined interface designed for personal use
- **Secure Sharing**: Share specific photos or albums via secure links

## Architecture

PhotoGen consists of:

- **Backend**: Python-based FastAPI application
- **Database**: PostgreSQL for reliable data storage
- **Storage**: Local file system for photos and generated images
- **AI Integration**: Seamless connection to local or remote InvokeAI instances

## Development Environment Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Node.js 18+ (for frontend development)
- InvokeAI (local installation or remote access)

### Backend Setup

See [backend/README.md](backend/README.md) for detailed backend setup instructions.

### Frontend Setup

*Frontend setup instructions will be added when development begins.*

## Development Guidelines

- All code should follow the project's style guide
- Write tests for new features
- Focus on maintaining a simple, focused user experience
- Avoid duplicating InvokeAI functionality

## Documentation

- Backend developer guide: `backend/docs/developer-guide.md`
- Project specifications: `docs/specs/`
- Progress tracker for current objective: `docs/development/`

## License

[MIT License](LICENSE)

---

## Project Status

PhotoGen is currently in early development (v0.1.0). Features and APIs may change without notice.