# TaskHub - Task Management API

TaskHub is a task management backend API built with FastAPI. The project is developed as a learning project to demonstrate clean code practices, layered architecture, dependency injection, API versioning, database integration, and automated testing.

## Tech Stack

- Python 3.12
- FastAPI 0.111+
- Pydantic v2
- SQLAlchemy 2.x (Async)
- Alembic
- PostgreSQL 16
- Redis 7 (planned integration)
- Docker & Docker Compose
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
- **Model Layer:** Defines database tables and relationships using SQLAlchemy ORM.
- **Core Layer:** Contains shared configuration, database connections, dependencies, and security components.

## Project Structure

```text
Taskhub-SampleApp/
├── alembic/
│   └── versions/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── projects.py
│   │       │   └── users.py
│   │       └── router.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   └── security.py
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
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

### 4. Configure Environment Variables

Create a `.env` file in the project root directory.

Example configuration:

```env
POSTGRES_DB=taskhub_db
POSTGRES_USER=taskhub_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_PORT=5432
```

Do not commit `.env` because it contains environment-specific configuration and credentials.

### 5. Start PostgreSQL with Docker

Make sure Docker Desktop or Docker Engine is running.

Start