# TaskHub - Task Management API

A RESTful Task Management API built with **FastAPI**, **SQLAlchemy 2.x**, **PostgreSQL**, and **Redis**.

TaskHub provides user authentication, workspace management, role-based access control (RBAC), project management, and asynchronous database operations.

---

## Tech Stack

| Category | Technology |
|---|---|
| Language | Python 3.12+ |
| Web Framework | FastAPI |
| Data Validation | Pydantic v2 |
| ORM | SQLAlchemy 2.x (Async) |
| Database | PostgreSQL 16 |
| Database Migrations | Alembic |
| Cache / Token Storage | Redis 7 |
| Authentication | JWT (PyJWT) |
| Password Hashing | pwdlib (Argon2) |
| Containerization | Docker & Docker Compose |
| Package Management | uv |
| Testing | Pytest, HTTPX |
| Code Formatting / Linting | Ruff |
| Static Type Checking | MyPy |

---

## Architecture

TaskHub follows a layered architecture to separate responsibilities and make the application easier to maintain and test.

```text
Client
  |
  v
FastAPI Application
  |
  v
API Layer (Routers / Dependencies)
  |
  v
Service Layer (Business Logic)
  |
  v
Repository Layer (Database Operations)
  |
  v
SQLAlchemy Async Session
  |
  v
PostgreSQL
```

### Main Layers

| Layer | Responsibility |
|---|---|
| API | Defines HTTP endpoints, validates requests, and returns responses |
| Dependencies | Provides authentication, authorization, database sessions, and services |
| Services | Implements application and business logic |
| Repositories | Encapsulates database queries and CRUD operations |
| Models | Defines SQLAlchemy database models and relationships |
| Schemas | Defines Pydantic request and response schemas |
| Core | Contains configuration, security, exceptions, database setup, and Redis integration |

### Database

- PostgreSQL 16 is used as the primary database.
- SQLAlchemy 2.x asynchronous ORM is used for database operations.
- Alembic manages database schema migrations.
- Integer auto-increment primary keys are used for database entities.

### Repository Pattern

Repositories encapsulate database operations and help separate persistence logic from business logic.

The application uses a generic base repository and specialized repositories for individual entities.

### Service Layer

Services contain business rules and coordinate repository operations.

Examples include:

- Authentication and token management.
- User management.
- Workspace and membership management.
- Project management.

### Database Migrations

Alembic is used to manage database schema changes.

Create a migration:

```bash
uv run alembic revision --autogenerate -m "migration message"
```

Apply migrations:

```bash
uv run alembic upgrade head
```

Check the current migration:

```bash
uv run alembic current
```

---

## Project Structure

```text
Taskhub-SampleApp/
│
├── app/
│   ├── api/
│   │   ├── dependencies.py
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py
│   │       │   ├── projects.py
│   │       │   ├── users.py
│   │       │   └── workspaces.py
│   │       └── router.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── constants.py
│   │   ├── database.py
│   │   ├── db_errors.py
│   │   ├── dependencies.py
│   │   ├── exceptions.py
│   │   ├── exception_handlers.py
│   │   ├── messages.py
│   │   ├── redis.py
│   │   └── security.py
│   │
│   ├── models/
│   │   ├── base.py
│   │   ├── comment.py
│   │   ├── enums.py
│   │   ├── label.py
│   │   ├── project.py
│   │   ├── task.py
│   │   ├── user.py
│   │   └── workspace.py
│   │
│   ├── repositories/
│   │   ├── base.py
│   │   ├── comment.py
│   │   ├── label.py
│   │   ├── project.py
│   │   ├── task.py
│   │   ├── user.py
│   │   └── workspace.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── base.py
│   │   ├── project.py
│   │   ├── user.py
│   │   └── workspace.py
│   │
│   ├── services/
│   │   ├── auth.py
│   │   ├── project.py
│   │   ├── user.py
│   │   └── workspace.py
│   │
│   └── main.py
│
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── tests/
│   ├── conftest.py
│   ├── test_admin_concurrency.py
│   ├── test_auth.py
│   ├── test_authorization.py
│   ├── test_projects.py
│   ├── test_redis_integration.py
│   ├── test_repositories.py
│   ├── test_users.py
│   └── test_workspaces.py
│
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── uv.lock
```

---

## Getting Started

### Prerequisites

Install the following tools before running the application:

- Python 3.12 or later
- uv
- Docker Desktop
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/nguyenthuylinh05/Taskhub-SampleApp.git
cd Taskhub-SampleApp
```

### 2. Install Dependencies

```bash
uv sync --all-groups
```

### 3. Configure Environment Variables

Create a `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

Update the environment variables in `.env` to match your local configuration.

Make sure the PostgreSQL and Redis connection settings are correct.

**Do not commit `.env` or expose secret values in the repository.**

### 4. Start Infrastructure Services

Start PostgreSQL and Redis using Docker Compose:

```bash
docker compose up -d
```

Check running containers:

```bash
docker compose ps
```

### 5. Run Database Migrations

```bash
uv run alembic upgrade head
```

### 6. Start the Application

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at:

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

---

## Authentication & Security

TaskHub uses JWT-based authentication.

### Password Security

- Passwords are hashed using Argon2 through pwdlib.
- Plain-text passwords are never stored in the database.
- Password verification is performed through the password hashing utility.

### JWT Authentication

The authentication system supports:

- Access tokens.
- Refresh tokens.
- Token type validation.
- Token expiration validation.
- Refresh token rotation and revocation using Redis.

Protected endpoints require an access token in the HTTP Authorization header:

```http
Authorization: Bearer <access_token>
```

### Authentication Flow

1. A user registers or logs in.
2. The API verifies the user's credentials.
3. The API issues access and refresh tokens.
4. The client sends the access token when accessing protected endpoints.
5. The refresh endpoint issues a new token pair when the refresh token is valid.
6. Logout revokes the refresh token.

---

## Role-Based Access Control (RBAC)

TaskHub implements authorization at both the system and workspace levels.

### System Roles

| Role | Description |
|---|---|
| ADMIN | System administrator with administrative privileges |
| MEMBER | Regular application user |

### Workspace Roles

| Role | Permissions |
|---|---|
| OWNER | Full workspace management, including membership management |
| EDITOR | Can create and update workspace projects |
| VIEWER | Can view workspace resources |

The workspace owner has OWNER access without requiring a separate membership record.

System administrators can access workspaces with administrative privileges.

### Authorization Dependencies

The application defines the following authorization dependencies in `app/api/dependencies.py`:

| Dependency | Responsibility |
|---|---|
| `get_current_user` | Retrieves the authenticated active user |
| `get_workspace_access` | Retrieves workspace access and the user's workspace role |
| `require_workspace_member` | Requires workspace membership or equivalent access |
| `require_workspace_editor` | Requires OWNER or EDITOR access |
| `require_workspace_owner` | Requires OWNER access |
| `require_admin` | Requires system ADMIN role |

The `WorkspaceAccess` data class contains the workspace and the user's effective workspace role.

---

## API Endpoints

All API endpoints are prefixed with:

```text
/api/v1
```

### Authentication

| Method | Endpoint | Description | Authentication |
|---|---|---|---|
| POST | `/auth/register` | Register a new user | Public |
| POST | `/auth/login` | Authenticate and obtain tokens | Public |
| POST | `/auth/refresh` | Refresh access and refresh tokens | Refresh token |
| POST | `/auth/logout` | Revoke refresh token | Authenticated |

### Users

#### Current User

| Method | Endpoint | Description |
|---|---|---|
| GET | `/users/me` | Get current user's profile |
| PATCH | `/users/me` | Update current user's profile |
| POST | `/users/me/change-password` | Change current user's password |

#### User Administration

These endpoints require the system ADMIN role.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/users/` | List users with pagination |
| GET | `/users/{user_id}` | Get a user by ID |
| POST | `/users/` | Create a user |
| PATCH | `/users/{user_id}` | Update a user |
| DELETE | `/users/{user_id}` | Delete a user |

### Workspaces

| Method | Endpoint | Description | Required Access |
|---|---|---|---|
| POST | `/workspaces` | Create a workspace | Authenticated |
| GET | `/workspaces` | List accessible workspaces with pagination | Authenticated |
| GET | `/workspaces/{workspace_id}` | Get workspace details | Member |
| PATCH | `/workspaces/{workspace_id}` | Update workspace | Owner / Editor |
| DELETE | `/workspaces/{workspace_id}` | Delete workspace | Owner |

#### Workspace Members

| Method | Endpoint | Description | Required Access |
|---|---|---|---|
| POST | `/workspaces/{workspace_id}/members` | Add a workspace member | Owner |
| GET | `/workspaces/{workspace_id}/members` | List workspace members | Member |
| DELETE | `/workspaces/{workspace_id}/members/{user_id}` | Remove a workspace member | Owner |

### Projects

Project endpoints are nested under a workspace.

Base path:

```text
/api/v1/workspaces/{workspace_id}/projects
```

| Method | Endpoint | Description | Required Access |
|---|---|---|---|
| POST | `/workspaces/{workspace_id}/projects` | Create a project | Owner / Editor |
| GET | `/workspaces/{workspace_id}/projects` | List workspace projects | Member |
| GET | `/workspaces/{workspace_id}/projects/{project_id}` | Get project details | Member |
| PATCH | `/workspaces/{workspace_id}/projects/{project_id}` | Update a project | Owner / Editor |
| DELETE | `/workspaces/{workspace_id}/projects/{project_id}` | Delete a project | Owner / Editor |

For request and response schemas, see the Swagger UI at `/docs`.

---

## Error Handling

The application uses centralized exception handling to return consistent HTTP error responses.

Common HTTP status codes include:

| Status Code | Meaning |
|---|---|
| 400 | Bad Request |
| 401 | Authentication required or invalid credentials/token |
| 403 | Insufficient permissions |
| 404 | Requested resource not found |
| 409 | Resource conflict, such as duplicate email |
| 422 | Request validation failed |
| 500 | Internal server error |

Examples of application-level errors include:

- Invalid credentials.
- Inactive user.
- Invalid refresh token.
- Permission denied.
- Resource not found.
- Duplicate email or other resource conflicts.
- Invalid business operations.

---

## Testing

The project uses Pytest and HTTPX to test API endpoints, business logic, repositories, authorization, and integrations.

Run the complete test suite:

```bash
uv run pytest -v
```

Run a specific test file:

```bash
uv run pytest tests/test_auth.py -v
```

Run authorization tests:

```bash
uv run pytest tests/test_authorization.py -v
```

Run workspace tests:

```bash
uv run pytest tests/test_workspaces.py -v
```

Run project tests:

```bash
uv run pytest tests/test_projects.py -v
```

### Test Coverage

The test suite includes:

| Test File | Coverage |
|---|---|
| `test_auth.py` | Registration, login, token validation, refresh, logout, and password-related behavior |
| `test_authorization.py` | Authentication requirements and system/workspace role permissions |
| `test_admin_concurrency.py` | Concurrent operations that protect the last active administrator |
| `test_users.py` | User profile, administration, pagination, and user deletion behavior |
| `test_workspaces.py` | Workspace CRUD, membership, role permissions, pagination, and deletion behavior |
| `test_projects.py` | Project CRUD and workspace-level authorization |
| `test_repositories.py` | Repository operations |
| `test_redis_integration.py` | Redis integration, refresh-token rotation, reuse detection, and revocation |

### Redis Integration Tests

Redis integration tests require a running Redis service.

The integration tests use Redis database **15** to isolate test data from the application's normal Redis database.

Run the Redis integration tests:

```bash
uv run pytest tests/test_redis_integration.py -v
```

Make sure the Redis connection settings in the test environment point to the intended test database.

---

## Code Quality

### Ruff

Run lint checks:

```bash
uv run ruff check .
```

### MyPy

Run static type checking:

```bash
uv run mypy app tests
```

Both tools are used to maintain code quality and catch potential issues before changes are submitted.

---

## Development Progress

The project is developed incrementally according to the FastAPI module curriculum.

| Day | Topic | Status |
|---|---|---|
| Day 1 | Core Setup & Architecture | Completed |
| Day 2 | SQLAlchemy 2.x Async & Alembic | Completed |
| Day 3 | Authentication & Security | Completed |
| Day 4 | Authorization & RBAC | Completed |

### Day 4 Verification

The Day 4 implementation and verification completed with the following results:

| Check | Result |
|---|---|
| Full Pytest suite | 83 passed |
| Ruff | All checks passed |
| MyPy (`app`) | No issues found |
| MyPy (`app tests`) | No issues found in 60 source files |

Day 4 includes workspace-level authorization, role-based access control, workspace membership management, project permissions, pagination, and protection against removing the last active administrator.

---

## Notes

- Use `.env.example` as the reference for environment configuration.
- Never commit `.env`, passwords, access tokens, refresh tokens, or other secrets.
- Run Alembic migrations after pulling changes that introduce database schema updates.
- Keep manual verification scripts out of the repository root. Automated tests belong in `tests/`.
- API request and response details can be inspected through Swagger UI at `/docs`.

---

## License

This project is developed for educational purposes as part of a FastAPI coursework assignment.
