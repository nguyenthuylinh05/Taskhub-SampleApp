# TaskHub – Task Management API

A RESTful Task Management API built with **FastAPI**, **SQLAlchemy 2.x**, **PostgreSQL**, and **Redis**.

TaskHub provides authentication, workspace and project management, task assignment, labels, comments, role-based access control (RBAC), task filtering, pagination, caching, and background email notifications.

The application follows a layered architecture and uses asynchronous database operations to provide a maintainable and extensible backend.

---

## Features

### Authentication and User Management
- User registration and login.
- JWT access and refresh tokens.
- Refresh token rotation and revocation using Redis.
- Secure password hashing with Argon2.
- Retrieve and update the current user's profile.
- Change password.
- Administrative user management.

### Workspace Management
- Create, retrieve, update, and delete workspaces.
- List accessible workspaces with pagination.
- Add, list, and remove workspace members.
- Manage workspace access through OWNER, EDITOR, and VIEWER roles.
- Restrict workspace updates and membership management to authorized owners.

### Project Management
- Create, retrieve, update, list, and delete projects.
- Organize projects within workspaces.
- Control project access through workspace permissions.
- Archive projects.
- Restrict write operations on archived projects where applicable.

### Task Management
- Create, retrieve through project task lists, update, and delete tasks.
- Assign tasks to workspace members.
- Manage task status, priority, and due dates.
- Search tasks by title and description.
- Filter tasks by status, priority, and assignee.
- Paginate task-list responses.
- Include associated labels in task responses.

### Labels and Comments
- Create and manage project-specific labels.
- Assign and remove labels from tasks.
- Enforce unique label names within each project.
- Create, list, update, and delete task comments.
- Enforce comment authorship and deletion permissions.
- Support pagination for label and comment lists.

### Caching
- Cache task-list responses using Redis.
- Include project, user, filters, search, pagination, and cache version in cache keys.
- Invalidate cached results after relevant data mutations.
- Fall back to PostgreSQL when Redis cache operations fail.
- Check resource authorization before accessing cached data.

### Background Notifications
- Send email notifications when a task is assigned or reassigned.
- Execute email delivery using FastAPI background tasks.
- Configure SMTP through environment variables.
- Keep task creation and assignment successful even when email delivery fails.

### API Documentation and Deployment
- Interactive Swagger UI.
- ReDoc documentation.
- OpenAPI Bearer authentication scheme.
- Documented common API error responses.
- Dockerized application.
- Docker Compose orchestration for FastAPI, PostgreSQL, Redis, and Alembic migrations.

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
## Development Progress

TaskHub was developed following the 8-day FastAPI Module Curriculum.

| Day | Topic | Status |
|---|---|---|
| Day 1 | Core Setup & Architecture | Completed |
| Day 2 | SQLAlchemy 2.x Async & Alembic | Completed |
| Day 3 | Authentication & Security | Completed |
| Day 4 | Authorization & RBAC | Completed |
| Day 5 | Task Management | Completed |
| Day 6 | Label & Comment Management | Completed |
| Day 7 | Search, Filtering, Pagination & Caching | Completed |
| Day 8 | Review, Refactoring & Optimization | Completed |

The curriculum topics are reflected in the current application architecture, API implementation, database layer, automated tests, and deployment configuration.

### Development and Verification

The following commands are used to verify the application:

```bash
uv run pytest -q
uv run ruff check .
uv run mypy app
git diff --check
docker compose config --quiet
```

These checks cover automated tests, linting, static type checking, Git whitespace validation, and Docker Compose configuration validation.
---

## Architecture

TaskHub follows a layered architecture to separate responsibilities and improve maintainability, testability, and code organization.

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
| Middleware | Handles cross-cutting HTTP concerns such as request logging |

### Database

- PostgreSQL 16 is the primary database.
- SQLAlchemy 2.x asynchronous ORM handles database operations.
- Alembic manages database schema migrations.
- Integer auto-increment primary keys are used for database entities.

### Repository Pattern

Repositories encapsulate database operations and separate persistence logic from business logic.

The application uses a generic base repository and specialized repositories for individual entities.

### Service Layer

Services contain business rules and coordinate repository operations.

Examples include:

- Authentication and token management.
- User management.
- Workspace and membership management.
- Project management.
- Task management.
- Label and comment management.
- Task-list caching and email notifications.

---

## Project Structure

```text
Taskhub-SampleApp/
│
├── app/
│   ├── api/
│   │   ├── dependencies.py
│   │   ├── openapi.py
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
│   │   ├── email.py
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
│   ├── test_openapi.py
│   ├── test_projects.py
│   ├── test_redis_integration.py
│   ├── test_repositories.py
│   ├── test_task_cache.py
│   ├── test_task_notifications.py
│   ├── test_tasks.py
│   ├── test_users.py
│   └── test_workspaces.py
│
├── .dockerignore
├── .env.example
├── .gitignore
├── alembic.ini
├── compose.yaml
├── Dockerfile
├── pyproject.toml
├── README.md
└── uv.lock
```

---

## Getting Started

### Prerequisites

For the full containerized deployment:

- Docker Desktop
- Git

For local Python development:

- Python 3.12+
- uv
- Docker Desktop for PostgreSQL and Redis

### 1. Clone the Repository

```bash
git clone https://github.com/nguyenthuylinh05/Taskhub-SampleApp.git
cd Taskhub-SampleApp
```

### 2. Configure Environment Variables

Copy the example environment file:

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

**Linux / macOS**

```bash
cp .env.example .env
```

Update `.env` with your local configuration.

At minimum, configure:

- `POSTGRES_PASSWORD`: A private PostgreSQL password.
- `JWT_SECRET_KEY`: A secret key containing at least 32 characters.

The values in `.env.example` are intended for local development only.

Never commit `.env`, real passwords, JWT secrets, or other credentials to version control.

### 3. Start the Full Stack with Docker Compose

Build and start the application:

```bash
docker compose up --build
```

Docker Compose starts the following services:

| Service | Responsibility |
|---|---|
| `db` | PostgreSQL database |
| `redis` | Redis cache and refresh-token storage |
| `migrate` | One-shot Alembic migration service |
| `app` | FastAPI application |

The application waits for PostgreSQL and Redis health checks. The migration service must complete successfully before the API application starts.

Database migrations are executed through the dedicated migration service. The application does not use `create_all()` to initialize the database schema.

### 4. Access the Application

Once the services are running:

| Resource | URL |
|---|---|
| API Health Check | http://127.0.0.1:8000/health |
| Swagger UI | http://127.0.0.1:8000/docs |
| ReDoc | http://127.0.0.1:8000/redoc |
| OpenAPI JSON | http://127.0.0.1:8000/openapi.json |

### 5. Monitor and Stop the Services

Check service status:

```bash
docker compose ps
```

View application logs:

```bash
docker compose logs -f app
```

View infrastructure and migration logs:

```bash
docker compose logs -f db redis migrate
```

Stop the stack:

```bash
docker compose down
```

This command preserves persistent database and Redis volumes.

**Warning:** Do not use `docker compose down -v` unless you intentionally want to delete the stored database and Redis data.

---

## Local Python Development

To run the FastAPI application directly on your machine while using Docker for PostgreSQL and Redis:

### 1. Install Dependencies

```bash
uv sync --all-groups
```

### 2. Start PostgreSQL and Redis

```bash
docker compose up -d db redis
```

### 3. Configure Local Connections

For local Python execution, use:

```env
POSTGRES_HOST=localhost
REDIS_HOST=localhost
```

Docker Compose overrides these connection settings inside its network and uses the service names `db` and `redis`.

### 4. Apply Database Migrations

```bash
uv run alembic upgrade head
```

### 5. Start the API

```bash
uv run uvicorn app.main:app --reload
```

The API is available at:

```text
http://127.0.0.1:8000
```

---

## Database Migrations

Alembic manages database schema changes.

Before running a standalone Alembic command, verify that `.env` points to the intended database.

The application uses `POSTGRES_DB` (default: `taskhub_db`). Standalone Alembic commands use `TASKHUB_DATABASE_URL` if configured; otherwise, they use the application database URL.

Pytest fixtures use a separate `POSTGRES_TEST_DB` (default: `taskhub_test_db`) and run migrations against it as part of the test workflow. The fixture does not create the test database itself.

Do not run test-database migrations manually outside the test workflow.

### Create a Migration

```bash
uv run alembic revision --autogenerate -m "migration message"
```

### Apply Migrations

```bash
uv run alembic upgrade head
```

### Check the Current Migration

```bash
uv run alembic current
```

For standalone commands, always confirm that the effective database URL selects the intended development database before proceeding.

### Label Uniqueness Migration

The project includes a migration that enforces unique label names within each project:

`05386ea537cb_add_unique_label_name_per_project.py`

Before adding the constraint `uq_labels_project_id_name`, the migration checks for existing duplicate project/label-name pairs.

If duplicates exist, the migration stops and requires manual resolution. It does not automatically delete or merge existing data.

---

## SMTP Email Notifications

Task-assignment email notifications are disabled by default.

To enable them, configure the following environment variables:

```env
EMAIL_NOTIFICATIONS_ENABLED=true
SMTP_HOST=your-smtp-host
SMTP_PORT=587
SMTP_SENDER_EMAIL=your-sender@example.com
```

Configure SMTP authentication if required:

```env
SMTP_USERNAME=your-username
SMTP_PASSWORD=your-password
```

For STARTTLS, use:

```env
SMTP_USE_STARTTLS=true
SMTP_USE_SSL=false
```

For implicit TLS, use:

```env
SMTP_USE_STARTTLS=false
SMTP_USE_SSL=true
```

The two TLS modes cannot be enabled simultaneously.

The sender skips delivery when no SMTP host is configured. SMTP credentials are read from environment configuration and are not included in API responses or application logs.

Task-assignment notifications are scheduled as FastAPI background tasks. The task write is committed before notification delivery is scheduled.

SMTP delivery failures are logged with the task ID and do not roll back an already committed task assignment.

---

## Authentication and Security

TaskHub uses JWT-based authentication and Argon2 password hashing.

### Password Security

- Passwords are hashed using Argon2 through `pwdlib`.
- Plain-text passwords are never stored in the database.
- Password verification uses the configured password hashing utility.

### JWT Authentication

The authentication system supports:

- Access tokens.
- Refresh tokens.
- Token type validation.
- Token expiration validation.
- Refresh token rotation.
- Refresh token revocation using Redis.
- Refresh-token reuse detection.

Protected endpoints require an access token in the HTTP Authorization header:

```http
Authorization: Bearer <access_token>
```

### Authentication Flow

1. A user registers or logs in.
2. The API verifies the user's credentials.
3. The API issues an access token and a refresh token.
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
| EDITOR | Can manage workspace projects, tasks, labels, and comments according to endpoint policies |
| VIEWER | Can view accessible workspace resources |

The workspace owner has OWNER access without requiring a separate membership record.

System ADMIN users are resolved as effective OWNERs for workspace access.

### Authorization Dependencies

The application defines authorization dependencies in `app/api/dependencies.py`.

| Dependency | Responsibility |
|---|---|
| `get_current_user` | Retrieves the authenticated active user |
| `get_workspace_access` | Retrieves workspace access and the user's effective workspace role |
| `require_workspace_member` | Requires workspace membership or equivalent access |
| `require_workspace_editor` | Requires OWNER or EDITOR access |
| `require_workspace_owner` | Requires OWNER access |
| `require_admin` | Requires the system ADMIN role |

The `WorkspaceAccess` data class contains the workspace and the user's effective workspace role.

Authorization is enforced at the API and service levels to protect resources and prevent unauthorized cross-workspace operations.

---

## API Endpoints

All API endpoints use the `/api/v1` prefix.

### API Overview

| Module | Main Operations |
|---|---|
| Authentication | Register, login, refresh, logout |
| Users | Current profile, password change, user administration |
| Workspaces | Create, list, retrieve, update, delete |
| Workspace Members | Add, list, remove members |
| Projects | Create, list, retrieve, update, delete |
| Tasks | Create, list, update, delete, assignment, filtering, pagination |
| Labels | Create, list, retrieve, update, delete, assign, remove |
| Comments | Create, list, update, delete |

For detailed request and response schemas, use Swagger UI at `/docs`.

### Authentication

| Method | Endpoint | Description | Authentication |
|---|---|---|---|
| POST | `/auth/register` | Register a new user | Public |
| POST | `/auth/login` | Authenticate and obtain tokens | Public |
| POST | `/auth/refresh` | Refresh access and refresh tokens | Refresh token |
| POST | `/auth/logout` | Revoke refresh token | Refresh token |

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
| PATCH | `/workspaces/{workspace_id}` | Update workspace | OWNER |
| DELETE | `/workspaces/{workspace_id}` | Delete workspace | OWNER |

#### Workspace Members

| Method | Endpoint | Description | Required Access |
|---|---|---|---|
| POST | `/workspaces/{workspace_id}/members` | Add a workspace member | OWNER |
| GET | `/workspaces/{workspace_id}/members` | List workspace members | Workspace access |
| DELETE | `/workspaces/{workspace_id}/members/{user_id}` | Remove a workspace member | OWNER |

### Projects

Project endpoints are nested under a workspace.

Base path:

```text
/api/v1/workspaces/{workspace_id}/projects
```

| Method | Endpoint | Description | Required Access |
|---|---|---|---|
| POST | `/workspaces/{workspace_id}/projects` | Create a project | OWNER / EDITOR |
| GET | `/workspaces/{workspace_id}/projects` | List workspace projects | Workspace access |
| GET | `/workspaces/{workspace_id}/projects/{project_id}` | Get project details | Workspace access |
| PATCH | `/workspaces/{workspace_id}/projects/{project_id}` | Update a project | OWNER / EDITOR |
| DELETE | `/workspaces/{workspace_id}/projects/{project_id}` | Delete a project | OWNER / EDITOR |

### Tasks

Task listing supports database-level keyword search, filtering, pagination, Redis caching, and eager-loaded label responses.

```http
GET /api/v1/projects/{project_id}/tasks
```

#### Query Parameters

| Parameter | Values | Behavior |
|---|---|---|
| `search` | String, 1–255 characters | Case-insensitive title and description search |
| `status` | Repeatable `TODO`, `IN_PROGRESS`, `IN_REVIEW`, `DONE` | Match any supplied status |
| `priority` | Repeatable `LOW`, `MEDIUM`, `HIGH`, `URGENT` | Match any supplied priority |
| `assignee_id` | Positive integer | Match the assigned workspace member |
| `page` | Integer, default `1` | Page number, minimum `1` |
| `limit` | Integer, default `10`, maximum `100` | Items per page |

Repeated `status` and `priority` values are supported. Parameters can be combined and apply to both the returned `total` and paginated `items`.

Whitespace-only search is rejected. Search input is trimmed, and SQL wildcard characters are treated literally.

#### Task List Response

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "limit": 10
}
```

#### Redis Cache Strategy

Task-list responses are cached in Redis.

Cache keys account for:

- Project ID.
- Authenticated user ID.
- Search query.
- Status and priority filters.
- Assignee ID.
- Page and limit.
- Project cache-generation version.

Authorization is checked before cache access.

Redis failures fall back to PostgreSQL so that cache availability does not become a requirement for reading task lists.

Successful task, label, project, workspace, and workspace-member mutations advance the affected project's cache-generation version after the database transaction commits. Old cache entries expire according to `REDIS_TASK_CACHE_TTL_SECONDS`.

#### Assignment Notifications

When `EMAIL_NOTIFICATIONS_ENABLED=true`, creating a task with an assignee or changing its assignee queues an email notification to the new assignee after the database commit.

Unassigned tasks and updates that leave the assignee unchanged do not trigger notifications.

### Labels and Comments

Labels belong to a project. Task-label assignments are limited to tasks and labels in the same project.

Comment authors are derived from the authenticated user. Clients cannot supply `author_id` or `created_at`.

#### Label Endpoints

| Method | Endpoint | Description | Required Access |
|---|---|---|---|
| POST | `/projects/{project_id}/labels` | Create a project label | OWNER / EDITOR |
| GET | `/projects/{project_id}/labels` | List project labels | Workspace access |
| GET | `/labels/{label_id}` | Get a label | Workspace access |
| PATCH | `/labels/{label_id}` | Update a label | OWNER / EDITOR |
| DELETE | `/labels/{label_id}` | Delete a label | OWNER / EDITOR |
| POST | `/tasks/{task_id}/labels/{label_id}` | Assign a label to a task | OWNER / EDITOR |
| DELETE | `/tasks/{task_id}/labels/{label_id}` | Remove a label from a task | OWNER / EDITOR |

#### Comment Endpoints

| Method | Endpoint | Description | Required Access |
|---|---|---|---|
| POST | `/tasks/{task_id}/comments` | Add a task comment | OWNER / EDITOR |
| GET | `/tasks/{task_id}/comments` | List task comments | Workspace access |
| PATCH | `/comments/{comment_id}` | Update a task comment | Comment author |
| DELETE | `/comments/{comment_id}` | Delete a task comment | Comment author / Workspace OWNER |

System administrators receive effective OWNER-level access through the workspace authorization policy.

VIEWER users can read accessible labels and comments but cannot create, update, assign, or remove them.

#### Label Rules

- Label names must be unique within a project.
- Creating or renaming a label to a name already used in the same project returns HTTP `409 Conflict`.
- The database enforces uniqueness using `uq_labels_project_id_name`.
- A label from a different project cannot be assigned to a task.
- Removing a label association that does not exist returns `404`.
- Deleting a label resource is a separate operation.

#### Comment Rules

- The authenticated user supplies the comment author identity.
- Request validation rejects client-supplied `author_id` and `created_at`.
- Comment content is limited to 5000 characters.
- OWNER and EDITOR users can create comments.
- VIEWER users can read comments but cannot create them.
- Only the comment author can update their own comment, including when their workspace role is VIEWER.
- Other users, including workspace OWNERs and system ADMINs, cannot update a comment they did not author.
- A comment can be deleted by its author or a workspace OWNER.
- System ADMIN users receive effective OWNER-level access.
- EDITOR and VIEWER users cannot delete another user's comment.
- A comment author who remains a workspace member can delete their own comment even if their role is VIEWER.

#### Archived Project Restrictions

Label and comment writes are rejected for archived projects.

This includes creating, updating, or deleting a label; assigning or removing a task-label association; and creating, updating, or deleting a comment.

Reading and listing remain available subject to workspace access.

#### Label and Comment Pagination

Label and comment list endpoints accept `page` and `limit` query parameters.

| Parameter | Default | Validation |
|---|---|---|
| `page` | `1` | Minimum `1` |
| `limit` | `10` | Between `1` and `100` |

Both endpoints return the following response structure:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "limit": 10
}
```

Examples:

```http
GET /api/v1/projects/{project_id}/labels?page=1&limit=10
GET /api/v1/tasks/{task_id}/comments?page=1&limit=10
```

---

## Error Handling

The application uses centralized exception handling to return consistent HTTP error responses.

### Common HTTP Status Codes

| Status Code | Meaning |
|---|---|
| 400 | Bad Request |
| 401 | Authentication required or invalid credentials/token |
| 403 | Insufficient permissions |
| 404 | Requested resource not found or inaccessible |
| 409 | Resource conflict, such as duplicate email or label name |
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

The API documentation includes common error responses for supported endpoints.

---

## Request Logging

TaskHub uses Pure ASGI middleware to record request path, response status, processing time, and request ID.

The middleware reuses a valid `X-Request-ID` header or generates a safe request ID, then returns it in the response header.

Application log records expose the active request ID as a `request_id` field.

`LOG_LEVEL` configures the `app` and `taskhub` namespace logger levels and TaskHub-owned handler levels.

Response logging levels:

| Response Status | Log Level |
|---|---|
| 2xx and 3xx | INFO |
| 4xx | WARNING |
| 5xx | ERROR |

Query strings, authorization headers, and exception details are excluded from TaskHub request-summary logs.

The root logger is set to `WARNING`, but Python does not reapply ancestor logger levels to records propagated from child loggers. Third-party child loggers explicitly configured at `DEBUG` or `INFO` may therefore reach host root handlers if those handlers accept the records. Existing host root handlers are left unchanged.

TaskHub keeps Uvicorn error logs at `WARNING` or higher.

Logging configuration and Uvicorn access-log suppression run during application lifespan startup. TaskHub requires ASGI lifespan; `lifespan=off` is not a supported deployment mode. If an operator overrides this behavior, logging must be configured externally and Uvicorn should be started with `--no-access-log` to avoid duplicate logs.

---

## Testing

TaskHub uses Pytest and HTTPX to test API endpoints, business logic, repositories, authorization, middleware, and integrations.

### Run the Complete Test Suite

```bash
uv run pytest -v
```

### Run a Specific Test File

```bash
uv run pytest tests/test_auth.py -v
```

### Run Authorization Tests

```bash
uv run pytest tests/test_authorization.py -v
```

### Run Workspace Tests

```bash
uv run pytest tests/test_workspaces.py -v
```

### Run Project Tests

```bash
uv run pytest tests/test_projects.py -v
```

### Test Coverage

| Test File | Coverage |
|---|---|
| `test_auth.py` | Registration, login, token validation, refresh, logout, and password-related behavior |
| `test_authorization.py` | Authentication requirements and system/workspace role permissions |
| `test_admin_concurrency.py` | Concurrent operations that protect the last active administrator |
| `test_exception_handlers.py` | Application exception responses, status codes, and authentication headers |
| `test_logging.py` | LOG_LEVEL validation, application logger levels, request IDs, handler preservation, and Uvicorn logging policy |
| `test_middleware.py` | Request logging, status-based log levels, request IDs, cancellation, and sensitive information protection |
| `test_openapi.py` | Swagger/ReDoc availability, BearerAuth OpenAPI security scheme, and endpoint response documentation |
| `test_users.py` | User profile, administration, pagination, and user deletion behavior |
| `test_workspaces.py` | Workspace CRUD, membership, role permissions, pagination, and deletion behavior |
| `test_projects.py` | Project CRUD and workspace-level authorization |
| `test_tasks.py` | Task CRUD, workspace roles, assignment, validation, filters, pagination, and archived-project rules |
| `test_task_cache.py` | Redis task-list caching, query canonicalization, version invalidation, and database fallback |
| `test_task_notifications.py` | Background task-assignment email scheduling and SMTP error handling |
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

### Test Database Configuration

Database-backed pytest fixtures use `POSTGRES_TEST_DB` (default: `taskhub_test_db`) and run Alembic migrations against that database.

Keep the test database separate from the development database selected by `POSTGRES_DB`.

The test fixture does not create the database itself.

---

## Code Quality

TaskHub uses Ruff and MyPy to maintain code quality and catch potential issues before changes are submitted.

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

---


## Configuration Reference

Environment variables are configured through `.env`. Use `.env.example` as the reference for available settings.

Important configuration groups include:

| Configuration | Purpose |
|---|---|
| PostgreSQL | Database host, port, name, username, and password |
| Redis | Redis host, port, database, and cache settings |
| JWT | Secret key and token expiration settings |
| SMTP | Email server, sender, credentials, and TLS settings |
| Application | API host, port, and environment settings |
| Logging | Application log level |
| Task Cache | Redis task-cache expiration settings |

Use private values for credentials and secrets. Do not commit `.env` to the repository.

---

## Development Guidelines

- Keep the layered architecture and separate API, service, and repository responsibilities.
- Use asynchronous database operations for database-backed application code.
- Manage database schema changes through Alembic migrations.
- Keep business rules in service classes rather than API routers.
- Enforce authentication and authorization before accessing protected resources or cached data.
- Keep automated tests in the `tests/` directory.
- Keep manual verification scripts out of the repository root.
- Update tests and API documentation when changing endpoint behavior.
- Never commit real environment secrets or credentials.

---

## Project Purpose

This project is developed for educational purposes as part of a FastAPI coursework assignment.
