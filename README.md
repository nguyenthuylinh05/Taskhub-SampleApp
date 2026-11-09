# TaskHub - Task Management API

TaskHub is a task management backend API built with FastAPI. The project is developed as a learning project to demonstrate clean code practices, layered architecture, dependency injection, API versioning, and automated testing.

## Tech Stack

- Python 3.12
- FastAPI
- Pydantic v2
- Uvicorn
- Pytest
- Ruff
- MyPy

## Project Architecture

The project follows a Layered Architecture to separate responsibilities and improve maintainability.

- **API Layer:** Handles HTTP requests, responses, and routing.
- **Schema Layer:** Defines request and response data structures using Pydantic.
- **Service Layer:** Contains application business logic.
- **Repository Layer:** Handles data access operations.
- **Core Layer:** Contains shared configuration, dependencies, and application-level components.

## Project Structure

```text
Taskhub-SampleApp/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       └── router.py
│   ├── core/
│   │   └── dependencies.py
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── tests/
│   └── test_projects.py
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## Getting Started

### 1. Clone Repository

```bash
git clone https://github.com/nguyenthuylinh05/Taskhub-SampleApp.git
cd Taskhub-SampleApp
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
```

Activate the virtual environment:

**Windows:**

```bash
.venv\Scripts\activate
```

**Linux/macOS:**

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -e ".[dev]"
```

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