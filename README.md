# FastAPI Input-Output Analysis Application

A highly scalable FastAPI application for Input-Output economic analysis with Microsoft Authentication integration and advanced matrix operations.

## Features

- ✅ **Input-Output Analysis** with economic matrix operations
- ✅ **FastAPI** with async/await support
- ✅ **SQLAlchemy** ORM with PostgreSQL
- ✅ **NumPy & SciPy** for matrix calculations
- ✅ **Pydantic** for data validation
- ✅ **Microsoft Azure AD Authentication** with JWT validation
- ✅ **Redis** for caching
- ✅ **Docker** & **Docker Compose** for containerization
- ✅ **Prometheus** metrics collection
- ✅ **Structured logging** with correlation IDs
- ✅ **Comprehensive testing** with pytest
- ✅ **Code quality** tools (Black, isort, flake8, mypy)
- ✅ **API Documentation** with Swagger/OpenAPI
- ✅ **Database migrations** with Alembic
- ✅ **CORS** and security middleware
- ✅ **Health checks** and monitoring endpoints
- ✅ **Observability** ready (Jaeger, Prometheus, Grafana)

## Project Structure

```
├── api/
│   ├── v1/
│   │   ├── __init__.py      # API v1 router
│   │   └── io.py            # IO analysis endpoints
│   └── health.py            # Health check endpoints
├── core/
│   ├── config.py            # Configuration settings
│   ├── auth.py              # Microsoft Auth validation
│   └── logging.py           # Logging configuration
├── db/
│   └── database.py          # Database connection
├── models/
│   └── models.py            # SQLAlchemy models (IOMatrix)
├── schemas/
│   └── io_schemas.py        # IO Pydantic schemas
├── services/
│   ├── io_service.py        # IO business logic
│   ├── matrix_service.py    # Matrix operations
│   └── data_service.py      # Data fetching from CSV/APIs
├── utils/
│   ├── cache.py             # Redis cache utilities
│   └── metrics.py           # Prometheus metrics
├── data/                    # CSV data files
│   ├── IODATA.csv          # Sample intermediate consumption data
│   ├── FD.csv              # Sample final demand data
│   └── sectors.csv         # Sample sector labels
├── tests/                   # Test files
├── monitoring/              # Observability configuration
└── main.py                  # FastAPI application
```

## Authentication

This application uses **Microsoft Azure AD** for authentication. The API expects JWT tokens from Microsoft in the Authorization header:

```
Authorization: Bearer <microsoft-jwt-token>
```

### Required Environment Variables:
```env
MICROSOFT_TENANT_ID=your-azure-tenant-id
MICROSOFT_CLIENT_ID=your-azure-client-id
MICROSOFT_AUDIENCE=your-audience (optional, defaults to client_id)
```

### Protected Endpoints (require authentication):
- `POST /api/v1/io/matrices` - Create IO matrix
- `PUT /api/v1/io/matrices/{id}` - Update IO matrix
- `DELETE /api/v1/io/matrices/{id}` - Delete IO matrix
- `PUT /api/v1/io/matrices/{id}/data` - Update IO data

### Public Endpoints:
- `GET /api/v1/io/matrices` - List IO matrices (public)
- `GET /api/v1/io/matrices/{id}` - Get IO matrix by ID (public)
- `GET /api/v1/io/matrices/{id}/intermediate-consumption` - Get IC data
- `GET /api/v1/io/matrices/{id}/final-demand` - Get FD data
- `POST /api/v1/io/matrices/{id}/operations/{operation}` - Perform matrix operations
- `POST /api/v1/io/validate-matrix` - Validate matrix data

## Input-Output Analysis Features

The core functionality of this application is **Input-Output (IO) Analysis** - a quantitative economic analysis technique used to model the interdependencies between different sectors of an economy.

### Key IO Endpoints:

#### Matrix Management:
- `POST /api/v1/io/matrices` - Create IO matrix (requires auth)
- `GET /api/v1/io/matrices` - List IO matrices (public)
- `GET /api/v1/io/matrices/{id}` - Get IO matrix by ID (public)  
- `PUT /api/v1/io/matrices/{id}` - Update IO matrix (requires auth)
- `DELETE /api/v1/io/matrices/{id}` - Delete IO matrix (requires auth)

#### Matrix Operations:
- `POST /api/v1/io/matrices/{id}/operations/{operation}` - Perform matrix operations
- `PUT /api/v1/io/matrices/{id}/data` - Update IO data (requires auth)
- `GET /api/v1/io/matrices/{id}/intermediate-consumption` - Get intermediate consumption data
- `GET /api/v1/io/matrices/{id}/final-demand` - Get final demand data
- `POST /api/v1/io/validate-matrix` - Validate matrix data format

#### Available Matrix Operations:
- `io_matrix` - Create full IO matrix (intermediate consumption + final demand)
- `intermediate_consumption` - Get intermediate consumption matrix
- `final_demand` - Get final demand matrix
- `technical_coefficients` - Calculate technical coefficients and Leontief inverse
- `multipliers` - Calculate economic multipliers

### Sample IO Matrix Structure:
```json
{
  "name": "3-Sector Economy",
  "description": "Sample IO matrix with Agriculture, Manufacturing, Services",
  "sectors": ["Agriculture", "Manufacturing", "Services"],
  "intermediate_consumption_data": [
    [50, 200, 100],
    [100, 300, 150],
    [25, 150, 200]
  ],
  "final_demand_data": [
    [400],
    [500],
    [300]
  ]
}
```

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone and setup the environment:**
   ```bash
   git clone <repository>
   cd input-output
   cp .env.example .env  # Update with your values
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Access the application:**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000 (admin/admin)
   - Jaeger: http://localhost:16686

### Local Development

1. **Setup Python environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # source venv/bin/activate  # On Linux/Mac
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start the application:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

### Items
- `POST /api/v1/items/` - Create item (requires Microsoft Auth)
- `GET /api/v1/items/` - List items (with pagination and filtering)
- `GET /api/v1/items/search` - Search items by title/description
- `GET /api/v1/items/{item_id}` - Get item by ID
- `PUT /api/v1/items/{item_id}` - Update item (requires Microsoft Auth)
- `DELETE /api/v1/items/{item_id}` - Delete item (requires Microsoft Auth)

### Health & Monitoring
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /` - Welcome message

## Configuration

Key environment variables in `.env`:

```env
# Application
APP_NAME=FastAPI Application
DEBUG=True

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/fastapi_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Microsoft Authentication
MICROSOFT_TENANT_ID=your-azure-tenant-id
MICROSOFT_CLIENT_ID=your-azure-client-id
MICROSOFT_AUDIENCE=your-audience
```

## Testing

Run tests with coverage:
```bash
pytest --cov=app --cov-report=html
```

## Code Quality

Format and lint code:
```bash
black app tests
isort app tests
flake8 app tests
mypy app
```

## Database Migrations

Initialize Alembic (if not done):
```bash
alembic init alembic
```

Create and run migrations:
```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## Monitoring & Observability

The application includes comprehensive monitoring:

- **Metrics**: Prometheus metrics at `/metrics`
- **Logging**: Structured JSON logging
- **Tracing**: OpenTelemetry compatible (Jaeger ready)
- **Health Checks**: Docker health checks and `/health` endpoint

## Production Deployment

1. **Environment Configuration:**
   - Set `DEBUG=False`
   - Use strong `SECRET_KEY`
   - Configure proper database URLs
   - Set up CORS origins correctly

2. **Security:**
   - Use HTTPS
   - Configure proper CORS settings
   - Set up rate limiting
   - Use environment-specific secrets

3. **Scaling:**
   - Use multiple worker processes
   - Add load balancer
   - Use database connection pooling
   - Implement caching strategies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run quality checks
6. Submit a pull request

## License

This project is licensed under the MIT License.
