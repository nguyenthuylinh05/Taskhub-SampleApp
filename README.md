# TaskHub - Task Management API

A RESTful Task Management API built with **FastAPI**, **SQLAlchemy 2.x (Async)**, **PostgreSQL**, and **Redis**. The project follows a layered architecture to keep the codebase maintainable, testable, and scalable.

## Tech Stack

| Category | Technology |
|---|---|
| Language | Python 3.12+ |
| Web Framework | FastAPI 0.111+ |
| ASGI Server | Uvicorn |
| ORM | SQLAlchemy 2.x (Async) |
| Database | PostgreSQL 16 |
| Database Migrations | Alembic |
| Data Validation | Pydantic v2 |
| Cache / Token Storage | Redis 7 |
| Authentication | JWT (PyJWT), Argon2 |
| Package Manager | uv |
| Testing | Pytest, pytest-asyncio, HTTPX |
| Code Quality | Ruff, Mypy |
| Containerization | Docker, Docker Compose |

## Architecture

The application follows a layered architecture:

```text
┌──────────────────────────────────────────────┐
│                  API Layer                   │
│       FastAPI Routers and Endpoints           │
├──────────────────────────────────────────────┤
│                Service Layer                 │
│       Business Logic and Validation          │
├──────────────────────────────────────────────┤
│              Repository Layer                │
│        Database Access and CRUD               │
├──────────────────────────────────────────────┤
│                  Core Layer                  │
│ Configuration, Security, Database, Redis,    │
│ Dependencies, Exceptions, and Constants      │
├──────────────────────────────────────────────┤
│                Data Layer                    │
│           PostgreSQL and Redis               │
└──────────────────────────────────────────────┘
```

### Layer Responsibilities

- **API Layer:** Defines HTTP endpoints, handles requests, and returns responses.
- **Service Layer:** Contains business logic and coordinates repositories.
- **Repository Layer:** Encapsulates database operations using SQLAlchemy 2.x async queries.
- **Core Layer:** Contains application configuration, database connections, dependencies, security utilities, Redis integration, constants, messages, and exception handling.
- **Data Layer:** Uses PostgreSQL for persistent application data and Redis for refresh-token storage.

## Project Structure

```text
Taskhub-SampleApp/
├── alembic/
│   ├── versions/
│   │   ├── 8007f1d7c3e6_create_initial_database_schema.py
│   │   ├── 8367cebbb3b8_add_foreign_key_indexes_and_delete_rules.py
│   │   └── 6f44128e9f83_add_unique_email_constraint_to_users.py
│   ├── env.py
│   └── script.py.mako
│
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py
│   │       │   ├── projects.py
│   │       │   └── users.py
│   │       └── router.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── constants.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── exception_handlers.py
│   │   ├── exceptions.py
│   │   ├── messages.py
│   │   ├── redis.py
│   │   └── security.py
│   │
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   └── main.py
│
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_projects.py
│   ├── test_redis_integration.py
│   ├── test_repositories.py
│   └── test_users.py
│
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── uv.lock
```

## Getting Started

### Prerequisites

Make sure the following tools are installed:

- Python 3.12+
- uv
- Docker Desktop
- Git

### 1. Clone the Repository

```powershell
git clone https://github.com/nguyenthuylinh05/Taskhub-SampleApp.git
cd Taskhub-SampleApp
```

### 2. Install Dependencies

```powershell
uv sync
```

### 3. Configure Environment Variables

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Update `.env` with your local configuration.

Generate a secure JWT secret:

```powershell
uv run python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Replace the development JWT secret in `.env` with the generated value.

**Important:** Never use the development secret in production or commit your actual `.env` file.

### 4. Start PostgreSQL and Redis

Start the services using Docker Compose:

```powershell
docker compose up -d
```

Check the running containers:

```powershell
docker compose ps
```

### 5. Run Database Migrations

Apply all database migrations:

```powershell
uv run alembic upgrade head
```

### 6. Start the Application

```powershell
uv run uvicorn app.main:app --reload
```

The API will be available at:

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Authentication and Security

The application implements JWT-based authentication with access tokens and refresh tokens.

### Features

- User registration and login.
- Password hashing using Argon2.
- JWT access-token authentication.
- Refresh-token storage using Redis.
- Refresh-token rotation.
- Refresh-token reuse detection.
- Individual session revocation.
- Revocation of all user refresh-token sessions.
- Password change with current-password verification.
- Protected user profile endpoints.

### Token Management

- Access tokens are used to authenticate API requests.
- Refresh tokens are stored and managed in Redis.
- Refresh-token rotation replaces the previous token with a new one.
- Reuse detection helps identify attempts to reuse an already rotated token.
- Logout revokes the corresponding refresh-token session.

## API Endpoints

All API endpoints use the `/api/v1` prefix.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Authenticate a user |
| POST | `/auth/refresh` | Refresh access and refresh tokens |
| POST | `/auth/logout` | Revoke the current refresh-token session |

### Users

| Method | Endpoint | Description |
|---|---|---|
| GET | `/users/me` | Get the current user's profile |
| PATCH | `/users/me` | Update the current user's profile |

### Projects

| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects` | List projects |
| POST | `/projects` | Create a project |
| GET | `/projects/{project_id}` | Get project details |
| PATCH | `/projects/{project_id}` | Update a project |
| DELETE | `/projects/{project_id}` | Delete a project |

For detailed request and response schemas, use the Swagger UI at `/docs`.

## Database

The project uses PostgreSQL 16 with SQLAlchemy 2.x asynchronous database operations.

### Database Migrations

Create a new migration:

```powershell
uv run alembic revision --autogenerate -m "migration_description"
```

Apply migrations:

```powershell
uv run alembic upgrade head
```

Rollback the latest migration:

```powershell
uv run alembic downgrade -1
```

Check the current migration revision:

```powershell
uv run alembic current
```

## Redis

Redis 7 is used for refresh-token storage and session management.

The application uses Redis to support:

- Refresh-token storage.
- Refresh-token rotation.
- Refresh-token reuse detection.
- Individual session revocation.
- Revocation of all refresh-token sessions belonging to a user.

Redis caching for application data is planned as a future enhancement.

## Testing

The project uses Pytest, pytest-asyncio, and HTTPX for automated testing.

### Run All Tests

```powershell
uv run pytest -v
```

### Run a Specific Test File

```powershell
uv run pytest tests/test_auth.py -v
```

### Redis Integration Tests

Redis integration tests use a dedicated Redis test database (DB 15) to verify refresh-token operations against a real Redis instance.

The tests cover:

- Refresh-token rotation.
- Refresh-token reuse detection.
- Refresh-token revocation.
- Revocation of all refresh-token sessions.

Run Redis integration tests:

```powershell
uv run pytest tests/test_redis_integration.py -v
```

Make sure PostgreSQL and Redis are running before executing integration tests.

The integration tests use isolated test data and should not require flushing the entire Redis database.

## Code Quality

### Ruff

Check code quality:

```powershell
uv run ruff check .
```

Automatically fix supported issues:

```powershell
uv run ruff check . --fix
```

### Mypy

Run static type checking:

```powershell
uv run mypy app/
```

## Development Progress

| Day | Topic | Status |
|---|---|---|
| Day 1 | Core setup and architecture | Completed |
| Day 2 | SQLAlchemy async and Alembic | Completed |
| Day 3 | Authentication and security | Completed |
| Day 4 | Authorization and RBAC | Planned |
| Day 5 | Middleware and exception handling | Planned |
| Day 6 | Redis caching and application configuration | Planned |
| Day 7 | Background tasks and logging | Planned |
| Day 8 | Docker and deployment | Planned |

## Roadmap

- Role-Based Access Control (RBAC).
- Workspace and project business logic.
- Task management and assignment.
- Labels and comments.
- Redis caching.
- Middleware and centralized exception handling.
- Background tasks and notifications.
- Structured logging.
- Docker deployment improvements.

## Development Notes

- Follow the layered architecture when adding new features.
- Keep business logic in the service layer.
- Keep database operations in repositories.
- Use Pydantic schemas for request validation and response serialization.
- Use Alembic for database schema changes.
- Add automated tests for new functionality.
- Keep manual check scripts inside the `tests/` directory; do not place them at the repository root.
- Never commit `.env` files or production secrets.

## License

This project is developed for educational purposes.