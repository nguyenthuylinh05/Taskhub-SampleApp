
# TaskHub - Task Management API

TaskHub is a task management backend API built with **FastAPI**. This learning project demonstrates layered architecture, asynchronous database operations, repository and service patterns, database migrations, dependency injection, JWT authentication, refresh-token session management, and automated testing.

## Tech Stack

| Category | Technology |
|---|---|
| Language | Python 3.12+ |
| API Framework | FastAPI 0.111+ |
| Data Validation | Pydantic v2 |
| Configuration | Pydantic Settings |
| ORM | SQLAlchemy 2.x (Async) |
| Database | PostgreSQL 16 |
| Database Driver | asyncpg |
| Migrations | Alembic |
| Password Hashing | pwdlib with Argon2 |
| Authentication | JWT with PyJWT |
| Refresh-token Storage | Redis 7 |
| Containerization | Docker Compose |
| Testing | Pytest, pytest-asyncio, HTTPX2 |
| Code Quality | Ruff, MyPy |
| Package Management | uv |

## Project Architecture

The application follows a layered architecture to separate responsibilities and improve maintainability, testability, and extensibility.

- **API Layer:** Handles HTTP requests, responses, and API routing.
- **Schema Layer:** Defines request and response data structures using Pydantic.
- **Service Layer:** Contains application business logic and coordinates repository operations.
- **Repository Layer:** Encapsulates database access and CRUD operations.
- **Model Layer:** Defines database entities and relationships using SQLAlchemy.
- **Core Layer:** Contains application configuration, database connections, dependencies, security utilities, Redis integration, constants, messages, and exception handling.

### Database Architecture

The project uses SQLAlchemy 2.x asynchronous ORM with PostgreSQL.

The database models include:

- User
- Workspace
- WorkspaceMember
- Project
- Task
- Label
- TaskLabel
- Comment

Primary keys use integer auto-incrementing identifiers.

### Repository Pattern

The repository layer provides reusable database operations through a generic base repository. Entity-specific repositories extend the base repository to implement additional data-access operations. Database operations use SQLAlchemy asynchronous sessions.

### Service Layer

The service layer separates business logic from HTTP endpoints and database access.

- `UserService` coordinates user-related operations.
- `AuthService` handles authentication workflows.
- `ProjectService` handles project-related operations.

### Database Migrations

Alembic manages database schema changes. Migration files are stored in `alembic/versions/`.

Apply migrations:

```powershell
uv run alembic upgrade head
```

Check the current migration revision:

```powershell
uv run alembic current
```

## Project Structure

```text
Taskhub-SampleApp/
├── alembic/
│   ├── versions/
│   │   ├── 8007f1d7c3e6_create_initial_database_schema.py
│   │   ├── 8367cebbb3b8_add_foreign_key_indexes_and_delete_rules.py
│   │   └── 6f44128e9f83_add_unique_email_constraint_to_users.py
│   ├── env.py
│   ├── README
│   └── script.py.mako
├── app/
│   ├── api/
│   │   ├── dependencies.py
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py
│   │       │   ├── projects.py
│   │       │   └── users.py
│   │       └── router.py
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
│   ├── models/
│   │   ├── base.py
│   │   ├── comment.py
│   │   ├── enums.py
│   │   ├── label.py
│   │   ├── project.py
│   │   ├── task.py
│   │   ├── user.py
│   │   └── workspace.py
│   ├── repositories/
│   │   ├── base.py
│   │   ├── comment.py
│   │   ├── label.py
│   │   ├── project.py
│   │   ├── task.py
│   │   ├── user.py
│   │   └── workspace.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── base.py
│   │   ├── project.py
│   │   └── user.py
│   ├── services/
│   │   ├── auth.py
│   │   ├── project.py
│   │   └── user.py
│   └── main.py
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_projects.py
│   ├── test_repositories.py
│   └── test_users.py
├── .env.example
├── .gitignore
├── alembic.ini
├── compose.yaml
├── pyproject.toml
├── uv.lock
└── README.md
```

The structure above reflects the Day 2 database layer and Day 3 authentication layer.

## Getting Started

### 1. Prerequisites

Install the following tools:

- Python 3.12 or newer
- uv
- Docker Desktop
- Git

### 2. Clone the Repository

```powershell
git clone https://github.com/nguyenthuylinh05/Taskhub-SampleApp.git
cd Taskhub-SampleApp
```

Switch to the branch you want to work with, if needed:

```powershell
git switch day-3-auth-security
```

### 3. Install Dependencies

Install project dependencies, including development dependencies:

```powershell
uv sync --all-extras
```

### 4. Configure Environment Variables

Create a local `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

Generate a secure JWT secret:

```powershell
uv run python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Set the generated value as `JWT_SECRET_KEY` in `.env`. Update the PostgreSQL password and other local settings as necessary.

Example configuration:

```dotenv
# Application
APP_NAME=TaskHub
APP_VERSION=0.1.0
ENVIRONMENT=development
DEBUG=true
API_V1_PREFIX=/api/v1

# PostgreSQL
POSTGRES_DB=taskhub_db
POSTGRES_USER=taskhub_user
POSTGRES_PASSWORD=your_local_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_TEST_DB=taskhub_test_db

# JWT
JWT_SECRET_KEY=replace_with_your_generated_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

The test database URL is derived from the PostgreSQL settings and `POSTGRES_TEST_DB`.

**Never commit your local `.env` file or real credentials.**

### 5. Start PostgreSQL and Redis

The Docker Compose configuration provides PostgreSQL 16 and Redis 7.

Start both services:

```powershell
docker compose up -d
```

Check their status:

```powershell
docker compose ps
```

The services are exposed on localhost using the configured PostgreSQL port and Redis port `6379`.

### 6. Apply Database Migrations

```powershell
uv run alembic upgrade head
```

Check the current revision:

```powershell
uv run alembic current
```

### 7. Run the Application

```powershell
uv run uvicorn app.main:app --reload
```

The application will be available at:

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Authentication & Security

TaskHub implements JWT-based authentication with access tokens and refresh tokens.

### Authentication Features

- User registration and login.
- Password hashing using Argon2.
- JWT access-token generation and validation.
- Refresh-token generation and storage in Redis.
- Refresh-token rotation.
- Refresh-token revocation during logout.
- Refresh-token reuse detection.
- Revocation of active refresh-token sessions when token reuse is detected.
- Password change with current-password verification.
- Session revocation after successful password change.
- Protected endpoints using FastAPI dependencies.
- Custom application exceptions and centralized exception handling.

### Token Configuration

| Setting | Default | Description |
|---|---:|---|
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access-token lifetime in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh-token lifetime in days |

### Authentication Flow

1. A user registers with an email address and password.
2. The password is hashed using Argon2 before being stored.
3. The user logs in with valid credentials.
4. The API returns an access token and a refresh token.
5. The refresh token is stored and tracked in Redis.
6. When the access token expires, the client can request a new token pair using the refresh token.
7. Refresh-token rotation invalidates the previous refresh token.
8. Reuse of a revoked refresh token triggers revocation of the user's active refresh-token sessions.

## API Endpoints

All versioned API endpoints use the `/api/v1` prefix.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register a new account |
| POST | `/api/v1/auth/login` | Authenticate and obtain tokens |
| POST | `/api/v1/auth/refresh` | Refresh access and refresh tokens |
| POST | `/api/v1/auth/logout` | Revoke a refresh token |

### Users

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/users/me` | Get the current authenticated user's profile |
| PATCH | `/api/v1/users/me` | Update the current authenticated user's profile |
| POST | `/api/v1/users/me/change-password` | Change the current user's password |
| GET | `/api/v1/users/` | Get paginated users |
| GET | `/api/v1/users/{user_id}` | Get a user by ID |
| POST | `/api/v1/users/` | Create a user |
| PATCH | `/api/v1/users/{user_id}` | Update a user |
| DELETE | `/api/v1/users/{user_id}` | Delete a user |

Protected endpoints require an access token in the HTTP Authorization header:

```http
Authorization: Bearer <access_token>
```

### Projects

Project endpoints are available under the versioned API router. Refer to Swagger UI at `/docs` for the currently implemented request and response schemas.

## Error Handling

The application uses custom exceptions derived from `AppException` and a centralized exception handler.

Authentication-related exceptions include:

- `EmailAlreadyRegistered`: HTTP 409
- `InvalidCredentials`: HTTP 401
- `InactiveUser`: HTTP 403
- `InvalidRefreshToken`: HTTP 401

Validation errors are handled by FastAPI and Pydantic.

## Testing

Tests are located in the `tests/` directory. The test configuration uses a dedicated PostgreSQL test database, applies database migrations, and uses transaction rollback to isolate test data.

Run the complete test suite:

```powershell
uv run pytest -v
```

Run a specific test module:

```powershell
uv run pytest tests/test_users.py -v
```

## Code Quality

### Ruff

Check code style and linting:

```powershell
uv run ruff check .
```

Format Python files:

```powershell
uv run ruff format .
```

Check formatting without modifying files:

```powershell
uv run ruff format --check .
```

### MyPy

Run static type checking:

```powershell
uv run mypy app
```

## Development Progress

| Day | Focus | Status |
|---|---|---|
| Day 1 | Core setup, project structure, API foundation | Completed |
| Day 2 | Database integration and repository layer | Completed |
| Day 3 | Authentication and security | In Progress |
| Day 4 | Authorization and Role-Based Access Control (RBAC) | Planned |

## Development Roadmap

Features planned for subsequent development stages:

- Role-based access control (RBAC).
- Workspace and project business logic.
- Task management and assignment workflows.
- Redis caching.
- Middleware and advanced exception handling.
- Background tasks and notifications.
- Logging and production configuration.
- Dockerized application deployment.

## Notes

- PostgreSQL is the selected database.
- Database operations use asynchronous SQLAlchemy sessions.
- Database schema changes should be managed through Alembic migrations.
- Do not commit local `.env` files or database credentials.
- Automated tests and manual checking scripts must be placed inside the `tests/` directory, not at the repository root.

## License

This project is developed for learning and educational purposes.
