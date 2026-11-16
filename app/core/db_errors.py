from sqlalchemy.exc import IntegrityError


def is_email_unique_violation(exc: IntegrityError) -> bool:
    """Check whether an IntegrityError is caused by duplicate user email."""
    original_error = exc.orig

    return (
        getattr(original_error, "sqlstate", None) == "23505"
        and getattr(original_error, "constraint_name", None) == "ix_users_email"
    )
