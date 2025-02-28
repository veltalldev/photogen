# Photo Gallery Backend

Backend service for the Photo Gallery application, built with FastAPI and PostgreSQL.

## Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Virtual environment tool (venv, conda, etc.)

### Installation

1. Clone the repository
2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
# On Windows: venv\Scripts\activate
# On Git Bash: source venv/Script/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root based on the template:
```
# See .env.template for all required variables
```

5. Create the PostgreSQL database:
```bash
createdb photo_gallery_dev
createuser -P photo_gallery_user
# Grant privileges to the user
```

### Running the Application

From the project root:
```bash
cd src
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

## Development

- API documentation: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- See `docs/developer-guide.md` for common pitfalls and best practices

## Project Structure

```
backend/
├── src/
│   ├── api/            # API routes
│   ├── core/           # Core configuration
│   ├── db/             # Database setup
│   ├── models/         # SQLAlchemy models
│   ├── repositories/   # Database access layer
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic
│   └── main.py         # Application entry point
├── logs/               # Application logs
├── tests/              # Test suite
├── .env                # Environment variables
└── requirements.txt    # Dependencies
``` 