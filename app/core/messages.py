"""Application-wide error messages."""

# Project
PROJECT_NOT_FOUND = "Project not found"
PROJECT_FIELD_CANNOT_BE_NULL = "Field cannot be null"
# Repository
CANNOT_DELETE_REFERENCED_RESOURCE = (
    "Cannot delete this resource because it is referenced by other records"
)
# User
USER_NOT_FOUND = "User not found"
EMAIL_ALREADY_REGISTERED = "Email already registered"
UPDATE_FIELDS_REQUIRED = "At least one field must be provided"
UPDATE_FIELDS_CANNOT_BE_NULL = "Fields cannot be null"
CURRENT_PASSWORD_INCORRECT = "Current password is incorrect"
NEW_PASSWORD_MUST_BE_DIFFERENT = (
    "New password must be different from current password"
)

# Workspace
WORKSPACE_NOT_FOUND = "Workspace not found"
WORKSPACE_MEMBER_NOT_FOUND = "Workspace member not found"
WORKSPACE_MEMBER_ALREADY_EXISTS = "User is already a workspace member"
WORKSPACE_OWNER_CANNOT_BE_MEMBER = (
    "Workspace owner cannot be assigned as a member"
)
WORKSPACE_OWNER_CANNOT_BE_REMOVED = "Workspace owner cannot be removed"
WORKSPACE_OWNER_ROLE_INVALID = "Workspace owner role cannot be assigned"