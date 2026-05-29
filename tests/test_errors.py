import pytest
from gorm.errors import GormError, DBError, RecordNotFound, InvalidFieldError, MigrationError


class TestErrors:
    def test_gorm_error_is_exception(self):
        assert issubclass(GormError, Exception)

    def test_db_error_inherits_gorm_error(self):
        assert issubclass(DBError, GormError)

    def test_record_not_found_is_catchable_as_gorm_error(self):
        try:
            raise RecordNotFound("no record")
        except GormError:
            pass

    def test_invalid_field_error_message(self):
        err = InvalidFieldError("bad field: x")
        assert "bad field" in str(err)

    def test_migration_error_message(self):
        err = MigrationError("table already exists")
        assert "table already exists" in str(err)
