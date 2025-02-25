# Development Environment Setup Guide

## System Requirements

### Hardware
- Modern development machine (8GB+ RAM recommended)
- NVIDIA GPU (RTX 3000 series or better) for InvokeAI
- Sufficient storage for photo library and development tools (100GB+ recommended)

### Software Prerequisites
1. **Core Development Tools**
   - Python 3.10+
   - Java Development Kit (for Flutter)
   - Git
   - VS Code (recommended) or preferred IDE

2. **Database**
   - PostgreSQL 14+
   - psql command line tools

3. **InvokeAI**
   - Latest stable version
   - CUDA toolkit compatible with your GPU

## Installation Steps

### 1. Backend Setup

#### Python Environment
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Verify FastAPI installation
uvicorn main:app --reload
```

#### Database Setup
```bash
# Create development database
createdb photo_gallery_dev

# Initialize schema
psql -d photo_gallery_dev -f migrations/schema/initial.sql

# Verify connection
psql -d photo_gallery_dev -c "\dt"
```

#### InvokeAI Configuration
1. Ensure InvokeAI is running and accessible at `http://localhost:9090`
2. Verify with a test request:
```bash
curl http://localhost:9090/api/v1/health
```

### 2. Frontend Setup

#### Flutter Installation
1. Install Flutter SDK from flutter.dev
2. Add Flutter to your PATH
3. Run Flutter doctor to verify installation:
```bash
flutter doctor
```

#### Project Setup
```bash
# Get dependencies
flutter pub get

# Run code generation if needed
flutter pub run build_runner build

# Start development server
flutter run -d chrome  # For web development
flutter run  # For native development
```

## Development Workflow

### Local Development
1. Start InvokeAI server
2. Start PostgreSQL database
3. Run backend:
```bash
uvicorn main:app --reload
```
4. Run frontend:
```bash
flutter run
```

### Testing

#### Backend Tests
```bash
# Run Python tests
pytest tests/

# Run specific test file
pytest tests/test_photo_service.py
```

#### Frontend Tests
```bash
# Run non-UI tests
flutter test test/services
flutter test test/repositories
```

### Debug Configuration

#### VS Code Settings
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload"],
      "jinja": true,
      "justMyCode": true
    },
    {
      "name": "Flutter",
      "request": "launch",
      "type": "dart",
      "flutterMode": "debug"
    }
  ]
}
```

## Common Issues & Solutions

### Backend
1. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check connection string in environment variables
   - Ensure database exists and schema is initialized

2. **InvokeAI Integration**
   - Verify InvokeAI server is running
   - Check INVOKEAI_BASE_URL in environment
   - Monitor GPU memory usage

### Frontend
1. **Flutter Build Issues**
   - Clear build cache: `flutter clean`
   - Regenerate dependencies: `flutter pub get`
   - Check for outdated packages

2. **Development Performance**
   - Close unnecessary developer tools
   - Monitor GPU memory when using InvokeAI
   - Consider reducing photo library size during development

## Next Steps After Setup

1. Verify core functionality:
   - Photo upload and display
   - Thumbnail generation
   - InvokeAI integration
   - Database operations

2. Configure development tools:
   - Set up IDE extensions
   - Configure debug points
   - Set up database visualization tools

3. Prepare test data:
   - Sample photo set
   - Test database entries
   - InvokeAI test prompts