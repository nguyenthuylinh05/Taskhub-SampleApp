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

Before running an Alembic command, verify that `.env` points to the intended
database. The application uses `POSTGRES_DB` (default `taskhub_db`); standalone
Alembic commands use `TASKHUB_DATABASE_URL` if set, otherwise they use the
application database URL. Pytest fixtures use the separate `POSTGRES_TEST_DB`
(default `taskhub_test_db`) and run `alembic upgrade head` against it as part of
the test workflow. The fixture does not create the database itself, and
test-database migrations should not be run manually outside that workflow.

PR7 adds
`alembic/versions/05386ea537cb_add_unique_label_name_per_project.py`. It checks
for duplicate project/label-name pairs before creating
`uq_labels_project_id_name`. If duplicates exist, the migration stops and
requires manual resolution; it does not delete or merge data.

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

For these standalone commands, confirm that the effective URL selects the
intended development database before proceeding. Unless `TASKHUB_DATABASE_URL`
is set, that database is selected by `POSTGRES_DB`.

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
│   │       │   ├── comments.py
│   │       │   ├── labels.py
│   │       │   ├── projects.py
│   │       │   ├── tasks.py
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
│   │   ├── logging.py
│   │   ├── logging_context.py
│   │   ├── messages.py
│   │   ├── redis.py
│   │   └── security.py
│   │
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── request_logging.py
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
│   │   ├── comment.py
│   │   ├── label.py
│   │   ├── pagination.py
│   │   ├── project.py
│   │   ├── task.py
│   │   ├── user.py
│   │   └── workspace.py
│   │
│   ├── services/
│   │   ├── auth.py
│   │   ├── comment.py
│   │   ├── label.py
│   │   ├── project.py
│   │   ├── task.py
│   │   ├── user.py
│   │   ├── workspace.py
│   │   └── workspace_access.py
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
│   ├── test_comments.py
│   ├── test_exception_handlers.py
│   ├── test_labels.py
│   ├── test_logging.py
│   ├── test_middleware.py
│   ├── test_projects.py
│   ├── test_redis_integration.py
│   ├── test_repositories.py
│   ├── test_tasks.py
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
`REDIS_TASK_CACHE_TTL_SECONDS` controls the task-list cache TTL and defaults to
60 seconds.

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
| EDITOR | Can manage workspace projects, tasks, labels, and comments |
| VIEWER | Can view workspace resources |

The workspace owner has OWNER access without requiring a separate membership record.

System ADMIN users are resolved as effective OWNERs for workspace access. In the
endpoint tables, `Workspace access` means an authenticated OWNER, EDITOR, or
VIEWER of that workspace, or a system ADMIN.

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

All endpoints use the `/api/v1` prefix.

| Module | Main operations |
|---|---|
| Authentication | Register, login, refresh, logout |
| Users | Current profile, password change, user administration |
| Workspaces | Create, list, retrieve, update, delete |
| Workspace Members | Add, list, remove members |
| Projects | Create, list, retrieve, update, delete |
| Tasks | Task CRUD, assignment, filtering, pagination |
| Labels | Create, list, retrieve, update, delete, assign, remove |
| Comments | Create, list, update, delete |

See Swagger UI at `/docs` for request and response schemas.

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
| GET | `/workspaces/{workspace_id}` | Get workspace details | Workspace access |
| PATCH | `/workspaces/{workspace_id}` | Update workspace | Owner / Editor |
| DELETE | `/workspaces/{workspace_id}` | Delete workspace | Owner |

#### Workspace Members

| Method | Endpoint | Description | Required Access |
|---|---|---|---|
| POST | `/workspaces/{workspace_id}/members` | Add a workspace member | Owner |
| GET | `/workspaces/{workspace_id}/members` | List workspace members | Workspace access |
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
| GET | `/workspaces/{workspace_id}/projects` | List workspace projects | Workspace access |
| GET | `/workspaces/{workspace_id}/projects/{project_id}` | Get project details | Workspace access |
| PATCH | `/workspaces/{workspace_id}/projects/{project_id}` | Update a project | Owner / Editor |
| DELETE | `/workspaces/{workspace_id}/projects/{project_id}` | Delete a project | Owner / Editor |

For request and response schemas, see the Swagger UI at `/docs`.

### Tasks

Task listing supports database-level keyword search, filtering, pagination,
Redis caching, and eager-loaded label responses:

```text
GET /api/v1/projects/{project_id}/tasks
```

Supported query parameters:

| Parameter | Values | Behavior |
|---|---|---|
| `search` | String, 1–255 characters | Case-insensitive title and description search |
| `status` | Repeatable `TODO`, `IN_PROGRESS`, `IN_REVIEW`, `DONE` | Match any supplied status |
| `priority` | Repeatable `LOW`, `MEDIUM`, `HIGH`, `URGENT` | Match any supplied priority |
| `assignee_id` | Positive integer | Match the assigned workspace member |
| `page` | Integer, default `1` | Page number, minimum `1` |
| `limit` | Integer, default `10`, maximum `100` | Items per page |

Repeated `status` and `priority` values are supported. The parameters can be
combined and apply to the returned `total` as well as the paginated `items`.
Whitespace-only search is rejected; search is trimmed and SQL wildcard
characters are treated literally.

The task-list response remains:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "limit": 10
}
```

Task-list entries are cached in Redis using the project, authenticated user,
query filters, search, page, limit, and a project cache-generation version.
Authorization is checked before cache access. Redis failures fall back to
PostgreSQL. Successful task and label mutations, project/workspace mutations,
and workspace-member removal advance the affected project's cache-generation
version after the database transaction commits; old entries expire according
to `REDIS_TASK_CACHE_TTL_SECONDS`.

### Labels and Comments

Labels belong to a project. Task-label assignment is limited to tasks in the
same project. Comment authors are taken from the authenticated user, and
clients cannot supply `author_id` or `created_at`.

| Method | Endpoint | Description | Required Access |
|---|---|---|---|
| POST | `/projects/{project_id}/labels` | Create a project label | Owner / Editor |
| GET | `/projects/{project_id}/labels` | List project labels | Workspace access |
| GET | `/labels/{label_id}` | Get a label | Workspace access |
| PATCH | `/labels/{label_id}` | Update a label | Owner / Editor |
| DELETE | `/labels/{label_id}` | Delete a label | Owner / Editor |
| POST | `/tasks/{task_id}/labels/{label_id}` | Assign a label to a task | Owner / Editor |
| DELETE | `/tasks/{task_id}/labels/{label_id}` | Remove a label from a task | Owner / Editor |
| POST | `/tasks/{task_id}/comments` | Add a task comment | Owner / Editor |
| GET | `/tasks/{task_id}/comments` | List task comments | Workspace access |
| PATCH | `/comments/{comment_id}` | Update a task comment (author only) | Comment author |
| DELETE | `/comments/{comment_id}` | Delete a task comment | Comment author / Workspace OWNER |

System administrators receive owner-level access through the existing
workspace authorization policy. Viewers can read accessible labels and
comments but cannot create, update, assign, or remove them.

Labels are project-scoped. Names must be unique within a project; creating or
renaming a label to a name already used in that project returns HTTP 409
Conflict. The database enforces this with
`uq_labels_project_id_name`. A label from a different project cannot be
assigned to a task; the API returns the same 404 response used for a missing or
inaccessible label. Removing a label association that does not exist also
returns 404. Deleting a label resource is a separate operation.

Comments can be created, listed, updated, and deleted. The authenticated user
supplies the author identity, and request validation rejects client-supplied
`author_id` or `created_at`. Comment content is limited to 5000 characters.
OWNER and EDITOR users can create comments. VIEWER users can read comments but
cannot create them. Only the comment author can update their own comment,
including when their workspace role is VIEWER. Other users, including
workspace OWNERs and system ADMINs, cannot update a comment they did not
author. Users without workspace access cannot update comments.
Comment deletion follows a separate authorization policy: the comment author
or a workspace OWNER can delete a comment. System ADMIN users receive
effective OWNER-level access. EDITOR and VIEWER users cannot delete another
user's comment. A comment author who is still a workspace member can delete
their own comment even if their role is VIEWER.

Label and comment writes are rejected for archived projects. This includes
creating, updating, or deleting a label; assigning or removing a task-label
association; and creating, updating, or deleting a comment. Reading and
listing remain available subject to workspace access.

The task, label, and comment services share workspace-access helpers. System
ADMIN users receive effective OWNER-level access; workspace OWNERs have
OWNER-level access, EDITORs can perform the supported writes, and VIEWERs are
read-only. Reusable service error messages and validation/pagination constants
are centralized in `app/core/messages.py` and `app/core/constants.py`.

#### Label and Comment Pagination

The label and comment list endpoints accept the `page` and `limit` query
parameters. `page` must be at least 1; `limit` must be between 1 and 100. The
defaults are `page=1` and `limit=10`. Both endpoints return this structure:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "limit": 10
}
```

For example:

```text
GET /api/v1/projects/{project_id}/labels?page=1&limit=10
GET /api/v1/tasks/{task_id}/comments?page=1&limit=10
```

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

## Request Logging

TaskHub uses a Pure ASGI middleware to record request path, response status,
processing time, and request ID. The middleware reuses a valid `X-Request-ID`
header or generates a safe ID, then returns it in the response header.

Application log records expose the active request ID as a `request_id` field.
`LOG_LEVEL` sets the `app` and `taskhub` namespace logger levels and
Taskhub-owned handler levels; descendant loggers that inherit those levels
follow that setting. `2xx` and `3xx` responses are logged at `INFO`, `4xx` at
`WARNING`, and `5xx` at `ERROR`.

The root logger is set to `WARNING`, but Python does not reapply ancestor logger
levels to records propagated from child loggers. A third-party child logger
explicitly set to `DEBUG` or `INFO` can therefore reach a host root handler if
that handler's level and filters accept it. Existing host root handlers are
left unchanged, so Taskhub cannot guarantee suppression of all third-party
`DEBUG`/`INFO` records while preserving host logging configuration. Hosts
control those records through their logger levels and handler policies.
Taskhub keeps Uvicorn error logs at `WARNING` or higher.

Query strings, authorization headers, and exception details are excluded from
Taskhub request-summary logs. Starlette re-raises unhandled exceptions after
the safe 500 response, so the ASGI server may log exception details and a
traceback. Do not put secrets in exception messages; manage server error-log
retention and redaction separately.

Logging configuration and Uvicorn access-log suppression run during application
lifespan startup. Taskhub requires ASGI lifespan; `lifespan=off` is not a
supported deployment mode. If an operator overrides this, configure logging
externally and use Uvicorn's `--no-access-log` option to avoid duplicate logs.

---

## Testing

The project uses Pytest and HTTPX to test API endpoints, business logic, repositories, authorization, middleware, and integrations.

Run the complete test suite:

```bash
uv run pytest -v
```

Database-backed pytest fixtures use `POSTGRES_TEST_DB` and run Alembic migrations
against that database. Keep it separate from the development database selected
by `POSTGRES_DB`.

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
| `test_exception_handlers.py` | Application exception responses, status codes, and authentication headers |
| `test_logging.py` | LOG_LEVEL validation, application logger levels, request IDs, handler preservation, and Uvicorn logging policy |
| `test_middleware.py` | Request logging, status-based log levels, request IDs, cancellation, and sensitive information protection |
| `test_users.py` | User profile, administration, pagination, and user deletion behavior |
| `test_workspaces.py` | Workspace CRUD, membership, role permissions, pagination, and deletion behavior |
| `test_projects.py` | Project CRUD and workspace-level authorization |
| `test_tasks.py` | Task CRUD, workspace roles, assignment, validation, filters, pagination, and archived-project rules |
| `test_labels.py` | Label CRUD, task associations, project boundaries, and role permissions |
| `test_comments.py` | Comment creation, listing, updating, validation, server-assigned authorship, deletion, and workspace-role permissions |
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
uv run mypy app
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
| Day 5 | Task Management | Completed |
| Day 6 | Label & Comment Management | Completed |
| Day 7 | Search, Filtering, Pagination & Cache | Completed |


### Day 6 Verification

Latest reported Day 6 checks:

| Check | Result |
|---|---|
| Full Pytest suite (`uv run pytest -q`) | 164 passed |
| Ruff (`uv run ruff check .`) | All checks passed |
| MyPy (`uv run mypy app`) | Success, no issues found in 65 source files |
| `git diff --check` | Passed |

Day 6 implementation and testing are complete. PR #7 has been merged into
the `followup/logging` branch, which has subsequently been merged into `main`.

### Day 7 Implementation

Day 7 introduces keyword search, filtering, pagination, and Redis caching for task lists:
- Keyword search: database-level search across task title and description with literal handling of SQL wildcard characters and case-insensitivity.
- Filtering: combined filtering by task status, priority, and assignee.
- Pagination: paginated task responses with total count, page, and limit parameters.
- Redis task-list caching: cached task list queries using project, user, query parameters hash, and cache version.
- Cache invalidation: version-based invalidation advancing on task, label, project, and workspace member mutations after database transaction commit.

### Day 7 Verification

| Check | Result |
|---|---|
| Full Pytest suite (`uv run pytest -v`) | 180 passed |
| Ruff (`uv run ruff check .`) | All checks passed |
| MyPy (`uv run mypy app`) | Success, no issues found in 65 source files |
| `git diff --check` | Passed |

Day 7 implementation and testing are locally verified. A Day 7 PR has not yet
been created or merged. Day 8 has not started.

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
