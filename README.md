# TaskHub - Task Management API

TaskHub is a task management backend API built with FastAPI. The project is developed as a learning project to demonstrate clean code practices, layered architecture, dependency injection, API versioning, and automated testing.

## Tech Stack

- Python 3.12
- FastAPI
- Pydantic v2
- Uvicorn
- Pytest
- HTTPX2
- Ruff
- MyPy

## Project Architecture

The application follows a layered architecture to separate responsibilities and improve maintainability, testability, and extensibility.

- **API Layer:** Handles HTTP requests, responses, and routing.
- **Schema Layer:** Defines request and response data structures using Pydantic.
- **Service Layer:** Contains application business logic.
- **Repository Layer:** Handles data access operations.
- **Core Layer:** Contains shared configuration, dependencies, and application-level components.

## Project Structure

```text
Taskhub-SampleApp/
├── alembic/
│   └── versions/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       └── router.py
│   ├── core/
│   │   └── dependencies.py
│   ├── repositories/
│   │   └── project.py
│   ├── schemas/
│   │   ├── base.py
│   │   └── project.py
│   ├── services/
│   │   └── project.py
│   └── main.py
├── tests/
│   ├── test_projects.py
│   └── test_repositories.py
├── .env.example
├── .gitignore
├── alembic.ini
├── compose.yaml
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

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at:

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Running Tests

Run the test suite:

```bash
pytest -v
```

Run tests with coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

## Code Quality

Check code style with Ruff:

```bash
ruff check .
```

Check formatting:

```bash
ruff format --check .
```

Run static type checking:

```bash
mypy app/
```

## Development Notes

- The application uses FastAPI dependency injection.
- API routes are organized under the `/api/v1` version prefix.
- The repository layer is currently designed to support the initial application architecture.
- Automated tests are maintained in the `tests/` directory.

## License

This project is developed for educational purposes.