# Photo Gallery Project

A self-hosted, single-user photo gallery application with integrated AI image generation capabilities.

## Overview

This application serves as both a portfolio project and a practical tool for personal use, providing an intuitive interface for browsing photos and generating variations using InvokeAI.

### Key Features

- **Photo Management**: Browse, organize, and share photos via secure URLs
- **AI Generation**: Create variations of images using integrated InvokeAI
- **Self-Hosted**: Complete control over your data with local hosting
- **Single-User Focus**: Streamlined for personal use

## Project Structure

```
/
├── backend/           # Python FastAPI backend
│   ├── app/           # Application code
│   ├── data/          # Data storage managed by backend
│   │   └── photos/    # Photo storage directories
│   │       ├── generated/
│   │       ├── uploaded/
│   │       └── thumbnails/
│   ├── tests/         # Backend tests
│   └── ...
├── frontend/          # Web-based user interface  
└── docs/              # Documentation and specifications
```

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- JDK 17 and Dart 3.7 for Flutter 3.29
- InvokeAI installation (local or remote via RunPod)

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  
# or venv\Scripts\activate on Windows
# or source venv/Scripts/activate in Git Bash

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python -m app.db.init

# Start development server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### InvokeAI Setup

Follow the [InvokeAI Integration Guide](docs/Updated%20InvokeAI%20Integration%20Contract%20Specification.md) for detailed setup instructions.

## Development

This project follows test-driven development (TDD) principles. Each component includes test implementation as part of its development cycle.

### Backend Development

See the [Backend Development Progress Tracker](docs/Photo%20Gallery%20Backend%20Development%20Progress%20Tracker.md) for current status and upcoming tasks.

### API Documentation

Once the backend is running, API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [InvokeAI](https://github.com/invoke-ai/InvokeAI) for the AI image generation capabilities
- All open-source projects that made this possible