class GormError(Exception):
    """Base exception for all gorm errors."""


class DBError(GormError):
    """Database-level errors (connection, execution)."""


class RecordNotFound(GormError):
    """Raised when .First() / .Last() / .Take() finds no record."""


class InvalidFieldError(GormError):
    """Raised when a Field definition is invalid."""


class MigrationError(GormError):
    """Raised when auto-migration encounters an issue."""
