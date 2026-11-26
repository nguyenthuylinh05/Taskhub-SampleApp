"""Application-wide error messages."""

# Project
PROJECT_NOT_FOUND = "Project not found"
PROJECT_ARCHIVED = "Cannot modify resources in an archived project"

# Repository
CANNOT_DELETE_REFERENCED_RESOURCE = (
    "Cannot delete this resource because it is referenced by other records"
)

# Label
LABEL_NOT_FOUND = "Label not found"
LABEL_NOT_ASSIGNED = "Label is not assigned to this task"
LABEL_NAME_ALREADY_EXISTS = "Label name already exists in this project"
LABEL_ALREADY_ASSIGNED = "Label is already assigned to this task"

# Comment
COMMENT_NOT_FOUND = "Comment not found"

# User
USER_NOT_FOUND = "User not found"
EMAIL_ALREADY_REGISTERED = "Email already registered"
USER_EMAIL_ALREADY_REGISTERED = "Email already registered"
UPDATE_FIELDS_REQUIRED = "At least one field must be provided"
UPDATE_FIELDS_CANNOT_BE_NULL = "Fields cannot be null"
USER_UPDATE_FIELDS_CANNOT_BE_NULL = "Update fields cannot be null"
CURRENT_PASSWORD_INCORRECT = "Current password is incorrect"
NEW_PASSWORD_MUST_BE_DIFFERENT = "New password must be different from current password"
CANNOT_DELETE_OWN_ACCOUNT = "You cannot delete your own account"
CANNOT_REMOVE_LAST_ACTIVE_ADMIN = "Cannot remove or deactivate the last active admin"
CANNOT_DELETE_LAST_ACTIVE_ADMIN = "Cannot delete the last active admin"
USER_INACTIVE = "Inactive user"

# Workspace
WORKSPACE_NOT_FOUND = "Workspace not found"
WORKSPACE_MEMBER_NOT_FOUND = "Workspace member not found"
WORKSPACE_MEMBER_ALREADY_EXISTS = "User is already a workspace member"
WORKSPACE_OWNER_CANNOT_BE_MEMBER = "Workspace owner cannot be assigned as a member"
WORKSPACE_OWNER_CANNOT_BE_REMOVED = "Workspace owner cannot be removed"
WORKSPACE_OWNER_ROLE_INVALID = "Workspace owner role cannot be assigned"

# Task
TASK_NOT_FOUND = "Task not found"
TASK_ASSIGNEE_NOT_IN_WORKSPACE = "Task assignee must be a workspace member"
TASK_DUE_DATE_MUST_BE_FUTURE = "Due date must be in the future"

# Task authorization and project state
TASK_ASSIGNEE_MUST_HAVE_WRITE_ACCESS = (
    "Task assignee must be a workspace owner or editor"
)
