# TaskHub - Task Management API

TaskHub is a task management backend API built with **FastAPI**. This project is developed as a learning project to demonstrate layered architecture, asynchronous database operations, repository and service patterns, database migrations, dependency injection, and automated testing.

## Tech Stack

| Category | Technology |
|---|---|
| Language | Python 3.12+ |
| API Framework | FastAPI |
| Data Validation | Pydantic v2 |
| Configuration | Pydantic Settings |
| ORM | SQLAlchemy 2.x (Async) |
| Database | PostgreSQL 16 |
| Database Driver | asyncpg |
| Migrations | Alembic |
| Password Hashing | pwdlib with Argon2 |
| Containerization | Docker Compose |
| Testing | Pytest, pytest-asyncio, HTTPX2 |
| Code Quality | Ruff, MyPy |
| Package Management | uv |

Redis 7 is planned for a later development stage and is not part of the current implementation.

## Project Architecture

The application follows a layered architecture to separate responsibilities and improve maintainability, testability, and extensibility.

- **API Layer:** Handles HTTP requests, responses, and API routing.
- **Schema Layer:** Defines request and response data structures using Pydantic.
- **Service Layer:** Contains application business logic and coordinates repository operations.
- **Repository Layer:** Encapsulates database access and CRUD operations.
- **Model Layer:** Defines database entities and relationships using SQLAlchemy.
- **Core Layer:** Contains application configuration, database connections, dependencies, security utilities, constants, and exception handling.

### Database Architecture

The project uses SQLAlchemy 2.x asynchronous ORM with PostgreSQL.

The current database models include:

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

The repository layer provides reusable database operations through a generic base repository.

Specific repositories extend the base repository to implement entity-specific data access.

Database operations use SQLAlchemy's asynchronous session.

### Service Layer

The service layer separates business logic from HTTP endpoints and database access.

For example, `UserService` coordinates user-related operations by using `UserRepository`.

### Database Migrations

Alembic manages database schema changes.

Migration files are stored in `alembic/versions/`. Apply migrations using:

```powershell
uv run alembic upgrade head
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
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── projects.py
│   │       │   └── users.py
│   │       └── router.py
│   ├── core/
│   │   ├── config.py
│   │   ├── constants.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── exceptions.py
│   │   ├── exception_handlers.py
│   │   ├── messages.py
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
│   │   ├── base.py
│   │   ├── project.py
│   │   └── user.py
│   ├── services/
│   │   ├── project.py
│   │   └── user.py
│   └── main.py
├── tests/
│   ├── conftest.py
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

## Getting Started

### 1. Prerequisites

Install the following tools before running the application:

- Python 3.12 or newer
- uv
- Docker Desktop
- Git

### 2. Clone the Repository

```powershell
git clone https://github.com/nguyenthuylinh05/Taskhub-SampleApp.git
cd Taskhub-SampleApp
```

To work with the Day 2 implementation:

```powershell
git switch day-2-database
```

### 3. Install Dependencies

Install the project dependencies, including development tools:

```powershell
uv sync --all-extras
```

### 4. Configure Environment Variables

Create a local `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

Update the database password and other settings in `.env` if necessary.

Example configuration:

```env
APP_NAME=TaskHub
APP_VERSION=0.1.0
ENVIRONMENT=development
DEBUG=true
API_V1_PREFIX=/api/v1

POSTGRES_DB=taskhub_db
POSTGRES_USER=taskhub_user
POSTGRES_PASSWORD=your_local_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_TEST_DB=taskhub_test_db
```

The test database URL is derived from the PostgreSQL settings and `POSTGRES_TEST_DB`.

### 5. Start PostgreSQL

Start the PostgreSQL service using Docker Compose:

```powershell
docker compose up -d db
```

Check the container status:

```powershell
docker compose ps
```

The PostgreSQL container uses the `postgres:16` image and exposes the database on the configured local port.

### 6. Apply Database Migrations

Apply all database migrations:

```powershell
uv run alembic upgrade head
```

Check the current migration revision:

```powershell
uv run alembic current
```

### 7. Run the Application

Start the FastAPI development server:

```powershell
uv run uvicorn app.main:app --reload
```

The application will be available at:

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Testing

The project uses Pytest and pytest-asyncio for automated testing.

Tests are located in the `tests/` directory.

Run the complete test suite:

```powershell
uv run pytest -v
```

Run a specific test module:

```powershell
uv run pytest tests/test_users.py -v
```

The test configuration uses a dedicated PostgreSQL test database. Tests apply database migrations and use transaction rollback to isolate test data.

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

## Current Development Progress

### Day 1 - Core Setup and Architecture

- Set up the FastAPI application.
- Implemented API versioning and routing.
- Established layered architecture.
- Added Pydantic schemas.
- Implemented dependency injection.
- Created initial project CRUD functionality.

### Day 2 - Database Integration

- Integrated PostgreSQL 16.
- Configured asynchronous SQLAlchemy 2.x.
- Created database models and relationships.
- Implemented generic and entity-specific repositories.
- Integrated Alembic migrations.
- Added database configuration using Pydantic Settings.
- Implemented user-related repository, service, schemas, and API endpoints.
- Added database integration tests.
- Improved exception handling and database integrity handling.

## Development Roadmap

The following features are planned for subsequent development stages:

- Authentication and JWT access/refresh tokens.
- Role-based access control (RBAC).
- Workspace and project business logic.
- Task management and assignment workflows.
- Redis caching.
- Middleware and advanced exception handling.
- Background tasks and notifications.
- Logging and production configuration.
- Dockerized application deployment.

## Notes

- PostgreSQL is the selected database for this project.
- Database operations use asynchronous SQLAlchemy sessions.
- Database schema changes should be managed through Alembic migrations.
- Do not commit local `.env` files or database credentials.
- Automated tests should be placed inside the `tests/` directory.
