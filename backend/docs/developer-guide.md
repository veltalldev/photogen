# Developer Documentation: Common Pitfalls and Best Practices

## Environment Configuration

### File Location
- Place `.env` file in the project root (`backend/`)
- The application expects to find it at `../env` relative to the `src/` directory
- Run the application from the `src/` directory with `cd src && uvicorn main:app --reload`

### Environment Variables
- `ALLOWED_ORIGINS`: Provide as comma-separated string (e.g., `http://localhost:3000,http://localhost:3001`)
- `UPLOAD_DIR`: Will be automatically created if it doesn't exist
- `SECRET_KEY`: Will be auto-generated if not provided

## Database Connection

### Connection Setup
- Connection string format: `postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}`
- Always test connections with a health check endpoint
- Use environment variables for all connection parameters

### Common SQLAlchemy Issues
- When using raw SQL with SQLAlchemy, always wrap queries in `text()`:
  ```python
  from sqlalchemy import text
  result = await db.execute(text("SELECT 1"))
  ```

- SQLAlchemy 2.0 async methods:
  - `await db.execute()` - Returns a result object
  - `result.scalar()` - Already returns the value (don't await this)
  - `result.scalars().all()` - For getting multiple results

## FastAPI Best Practices

### Application Structure
- Run the application from inside the `src` directory
- Use dependency injection for database sessions
- Use the lifespan context manager for startup/shutdown events

### Error Handling
- Always include global exception handlers
- Log exceptions with `exc_info=True` for stack traces
- Return standardized error responses

## Troubleshooting

### "Module not found" errors
- Check that you're running from the correct directory
- Ensure all `__init__.py` files exist
- Consider using `--app-dir` with uvicorn

### Database connection issues
- Verify PostgreSQL service is running
- Test connection with `psql` command line
- Check credentials in `.env` file
- Ensure database and user exist with proper permissions

### CORS errors
- Check `ALLOWED_ORIGINS` in `.env` file
- Ensure frontend is running on the allowed origin
- Look for CORS errors in browser console

## Development Workflow

### Running the application
```bash
# From backend directory
cd src
uvicorn main:app --reload
```

### Testing endpoints
```bash
# Health check
curl http://localhost:8000/health

# Or using browser
# Visit http://localhost:8000/docs for Swagger UI
``` 