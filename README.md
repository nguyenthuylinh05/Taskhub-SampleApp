# TaskHub - Task Management API

TaskHub is a task management backend API built with FastAPI. This project is developed as a learning project to demonstrate clean code practices, layered architecture, dependency injection, API versioning, database integration, authentication, authorization, security, and automated testing.

## Tech Stack

- Python 3.12
- FastAPI 0.111+
- Pydantic v2
- SQLAlchemy 2.x (Async)
- Alembic
- PostgreSQL 16
- Redis 7
- PyJWT
- Argon2 password hashing
- Docker & Docker Compose
- Uvicorn
- Pytest
- Ruff
- MyPy

## Project Architecture

The project follows a Layered Architecture to separate responsibilities and improve maintainability.

- **API Layer:** Handles HTTP requests, responses, routing, and authorization dependencies.
- **Schema Layer:** Defines request and response data structures using Pydantic.
- **Service Layer:** Contains application business logic.
- **Repository Layer:** Handles data access operations.
- **Model Layer:** Defines database tables, relationships, and enums using SQLAlchemy.
- **Core Layer:** Contains shared configuration, database connections, dependencies, exception handling, Redis integration, and security components.

## Project Structure

```text
Taskhub-SampleApp/
├── alembic/
│   └── versions/
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
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── exception_handlers.py
│   │   ├── exceptions.py
│   │   ├── redis.py
│   │   └── security.py
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── user.py
│   │   └── workspace.py
│   ├── services/
│   │   ├── auth.py
│   │   └── workspace.py
│   └── main.py
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_authorization.py
│   ├── test_projects.py
│   ├── test_repositories.py
│   └── test_workspaces.py
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

Using Python:

```bash
python -m venv .venv
```

Activate the virtual environment:

**Windows:**

```powershell
.venv\Scripts\activate
```

**Linux/macOS:**

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

This project uses `uv` for dependency management.

Install `uv` if it is not already installed:

```bash
pip install uv
```

Install project dependencies:

```bash
uv sync --extra dev
```

Alternatively, install using pip:

```bash
pip install -e ".[dev]"
```

### 4. Configure Environment Variables

Create a `.env` file from the example:

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

**Linux/macOS:**

```bash
cp .env.example .env
```

Generate a secure JWT secret:

```bash
uv run python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Update `.env` with the generated secret and your database configuration.

Example:

```env
# Application
APP_NAME=TaskHub
APP_VERSION=0.1.0
ENVIRONMENT=development
DEBUG=true
API_V1_PREFIX=/api/v1

# PostgreSQL
POSTGRES_DB=taskhub_db
POSTGRES_USER=taskhub_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# JWT
JWT_SECRET_KEY=your_generated_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

Do not commit `.env` because it contains environment-specific configuration and credentials.

### 5. Start PostgreSQL and Redis with Docker

Make sure Docker Desktop or Docker Engine is running.

Start the services:

```bash
docker compose up -d
```

Check running containers:

```bash
docker compose ps
```

The application uses PostgreSQL for persistent data storage and Redis for refresh-token session management.

When running the application directly on your host machine, configure the database and Redis hosts according to the exposed Docker ports. When running the application inside Docker Compose, use the corresponding service hostnames.

### 6. Run Database Migrations

Apply Alembic migrations:

```bash
uv run alembic upgrade head
```

### 7. Run the Application

Start the FastAPI development server:

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

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
- Active-user validation for protected endpoints.

### Token Configuration

| Setting | Default | Description |
|---|---:|---|
| `JWT_ALGORITHM` | HS256 | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 15 | Access-token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh-token lifetime |

The application validates the JWT secret, signing algorithm, and token expiration configuration during startup.

### Authentication Flow

1. A user registers with an email address and password.
2. The password is hashed using Argon2 before being stored.
3. The user logs in with valid credentials.
4. The API returns an access token and a refresh token.
5. The refresh token is stored and tracked in Redis.
6. When the access token expires, the client can request a new token pair using the refresh token.
7. Refresh-token rotation invalidates the previous refresh token.
8. Reuse of a revoked refresh token triggers revocation of the user's active refresh-token sessions.

## Authorization & Role-Based Access Control (RBAC)

TaskHub implements role-based access control to restrict administrative operations and workspace resources.

### User Roles

The system defines two application-level user roles:

| Role | Description |
|---|---|
| `ADMIN` | Has administrative privileges and can access workspace resources with owner-level permissions. |
| `MEMBER` | Standard authenticated user. |

Administrative user-management endpoints require the `ADMIN` role.

Regular users can access and update their own profiles and change their own passwords.

The system also prevents an administrator from deleting their own account or demoting, deactivating, or removing the last active administrator through the protected user-management operations.

### Workspace Roles

Workspace-level permissions are separate from application-level user roles.

| Role | Read Workspace | Edit Workspace | Manage Members |
|---|---|---|---|
| `OWNER` | Yes | Yes | Yes |
| `EDITOR` | Yes | Yes | No |
| `VIEWER` | Yes | No | No |

Workspace ownership is determined by the workspace's `owner_id`. The owner does not need a separate membership record.

### Authorization Rules

- Only authenticated users can access protected workspace endpoints.
- Workspace owners have full control over their workspaces.
- Workspace editors can access and edit workspace resources but cannot manage members.
- Workspace viewers have read-only workspace access.
- Non-members cannot access private workspace resources.
- Only workspace owners can add or remove members.
- The workspace owner cannot be added or removed as a regular member.
- The `OWNER` role cannot be assigned through the member-management endpoint.
- Application administrators bypass workspace-level role restrictions.
- Inaccessible or nonexistent workspaces return HTTP 404.
- Authenticated users without sufficient permissions receive HTTP 403.

Authorization is implemented using reusable FastAPI dependencies, including:

- `get_workspace_role`
- `require_workspace_member`
- `require_workspace_editor`
- `require_workspace_owner`
- `require_admin`

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

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| GET | `/api/v1/users/me` | Authenticated | Get current user's profile |
| PATCH | `/api/v1/users/me` | Authenticated | Update current user's profile |
| POST | `/api/v1/users/me/change-password` | Authenticated | Change current user's password |
| GET | `/api/v1/users/` | ADMIN | Get paginated users |
| GET | `/api/v1/users/{user_id}` | ADMIN | Get user by ID |
| POST | `/api/v1/users/` | ADMIN | Create a user |
| PATCH | `/api/v1/users/{user_id}` | ADMIN | Update a user |
| DELETE | `/api/v1/users/{user_id}` | ADMIN | Delete a user |

### Workspaces

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| POST | `/api/v1/workspaces/` | Authenticated | Create a workspace |
| GET | `/api/v1/workspaces/` | Authenticated | List workspaces owned or joined by the current user |
| GET | `/api/v1/workspaces/{workspace_id}` | Workspace member | Get workspace details |
| PATCH | `/api/v1/workspaces/{workspace_id}` | OWNER | Update workspace |
| DELETE | `/api/v1/workspaces/{workspace_id}` | OWNER | Delete workspace |
| POST | `/api/v1/workspaces/{workspace_id}/members` | OWNER | Add a workspace member |
| GET | `/api/v1/workspaces/{workspace_id}/members` | Workspace member | List workspace members |
| DELETE | `/api/v1/workspaces/{workspace_id}/members/{user_id}` | OWNER | Remove a workspace member |

### Projects

Project endpoints are available under the versioned API router. See Swagger UI at `/docs` for the current request and response schemas.

### Authorization Header

Protected endpoints require an access token in the HTTP Authorization header:

```http
Authorization: Bearer <access_token>
```

Use the access token returned by the login or refresh endpoint. Refresh tokens are intended for the refresh flow and must not be used as access tokens.

## Error Handling

The application uses custom exceptions derived from `AppException` and a centralized exception handler.

Examples include:

| Exception | HTTP Status | Description |
|---|---:|---|
| `EmailAlreadyRegistered` | 409 | Email address is already registered |
| `InvalidCredentials` | 401 | Invalid login credentials |
| `InactiveUser` | 403 | User account is inactive |
| `InvalidRefreshToken` | 401 | Refresh token is invalid |
| `PermissionDenied` | 403 | Insufficient permissions |
| `ResourceNotFound` | 404 | Requested resource does not exist |
| `ConflictError` | 409 | Resource conflict |
| `InvalidOperation` | 400 | Operation is not allowed |

Validation errors are handled by FastAPI and Pydantic.

## Testing & Code Quality

The project includes automated tests for authentication, authorization, workspace operations, repositories, and project endpoints.

Run the complete test suite:

```bash
uv run pytest -v
```

Run Ruff:

```bash
uv run ruff check .
```

Run MyPy:

```bash
uv run mypy app tests
```

### Latest Verification Results

| Check | Result |
|---|---|
| Ruff | Passed |
| MyPy | Passed — 52 source files |
| Pytest | 53 passed |
| Test failures | 0 |

The test suite currently verifies:

- User registration and authentication.
- Access-token and refresh-token behavior.
- Refresh-token rotation and revocation.
- Password change and session security.
- Administrative user-management permissions.
- Workspace role resolution.
- Workspace access restrictions.
- Workspace CRUD operations.
- Workspace member management.
- Duplicate membership and invalid-operation handling.

## Development Progress

| Day | Focus | Status |
|---|---|---|
| Day 1 | Core setup, project structure, API foundation | Completed |
| Day 2 | Database integration and repository layer | Completed |
| Day 3 | Authentication and security | Completed |
| Day 4 | Authorization and Role-Based Access Control (RBAC) | Completed — 53 tests passed |

## License

This project is developed for learning and educational purposes.