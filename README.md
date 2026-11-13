# TaskHub - Task Management API

TaskHub is a task management backend API built with FastAPI. This project is developed as a learning project to demonstrate clean code practices, layered architecture, dependency injection, API versioning, configuration management, request validation, custom exception handling, and automated testing.

This branch covers **Day 1 – Core Setup and Architecture** of the TaskHub development roadmap.

## Tech Stack

- Python 3.12+
- FastAPI 0.111+
- Pydantic v2
- Pydantic Settings
- Uvicorn
- Pytest
- HTTPX2
- Ruff
- MyPy

## Project Architecture

The application follows a layered architecture to separate responsibilities and improve maintainability, testability, and extensibility.

| Layer | Responsibility |
|---|---|
| API Layer | Handles HTTP requests, responses, and API routing. |
| Schema Layer | Defines and validates request and response data using Pydantic. |
| Service Layer | Contains application-level business logic. |
| Repository Layer | Abstracts data access operations. |
| Core Layer | Provides application configuration, dependencies, constants, exceptions, and shared components. |

### Request Flow

A typical request follows this flow:

1. The API endpoint receives the HTTP request.
2. Pydantic schemas validate the incoming data.
3. The endpoint obtains the required service through dependency injection.
4. The service executes the application logic.
5. The repository handles data access.
6. The API returns the appropriate response.

## Features Implemented

- FastAPI application initialization.
- Application lifespan management.
- Versioned API routing with the `/api/v1` prefix.
- Layered application architecture.
- Dependency injection for services and repositories.
- Project CRUD endpoints:
  - Create a project.
  - Retrieve projects.
  - Update a project.
  - Delete a project.
- Pydantic v2 request and response validation.
- Shared schema validation and whitespace normalization.
- Application configuration using Pydantic Settings.
- Centralized application constants and error messages.
- Custom application exceptions.
- Centralized exception handlers.
- Interactive API documentation through Swagger UI and ReDoc.
- Automated API tests.

## Project Structure

```text
Taskhub-SampleApp/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   └── projects.py
│   │       └── router.py
│   ├── core/
│   │   ├── config.py
│   │   ├── constants.py
│   │   ├── dependencies.py
│   │   ├── exceptions.py
│   │   ├── exception_handlers.py
│   │   └── messages.py
│   ├── repositories/
│   │   └── project.py
│   ├── schemas/
│   │   ├── base.py
│   │   └── project.py
│   ├── services/
│   │   └── project.py
│   └── main.py
├── tests/
│   └── test_projects.py
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.12 or later.
- Git.
- uv package manager.

### 1. Clone the Repository

```bash
git clone https://github.com/nguyenthuylinh05/Taskhub-SampleApp.git
cd Taskhub-SampleApp
```

To use the Day 1 implementation:

```bash
git switch day-1-core-setup
```

### 2. Install Dependencies

Install project dependencies and development tools:

```bash
uv sync --all-extras
```

### 3. Configure Environment Variables

Copy the example environment file:

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

Review the `.env` file and adjust application settings if necessary.

### 4. Run the Application

Start the development server:

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at:

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## API Versioning

All API endpoints are organized under the `/api/v1` prefix.

Example:

```text
/api/v1/projects
```

## Running Tests

Run the complete test suite:

```bash
uv run pytest -v
```

Run tests with coverage:

```bash
uv run pytest --cov=app --cov-report=term-missing
```

## Code Quality

Check code style with Ruff:

```bash
uv run ruff check .
```

Check code formatting:

```bash
uv run ruff format --check .
```

Run static type checking with MyPy:

```bash
uv run mypy app
```

## Development Notes

- The application uses FastAPI dependency injection.
- API routes are organized under the `/api/v1` version prefix.
- Application settings are managed centrally using Pydantic Settings.
- Request validation is implemented with Pydantic v2.
- Application errors are handled through custom exceptions and centralized exception handlers.
- The Project repository currently uses in-memory storage.
- PostgreSQL, SQLAlchemy async integration, and Alembic migrations are introduced in the subsequent database development phase.
- Automated tests are maintained in the `tests/` directory.

## Development Roadmap

| Day | Scope |
|---|---|
| Day 1 | Core setup and application architecture |
| Day 2 | Async database integration and Alembic migrations |
| Day 3 | Authentication and JWT |
| Later days | Authorization, caching, middleware, background tasks, and deployment |

## License

This project is developed for educational purposes.
