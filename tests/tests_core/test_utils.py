import pytest

from src.core.utils import str_to_bool


class TestStrToBool:
    """Tests for the str_to_bool helper function."""

    def test_true_string_returns_true(self):
        """Test that 'True' is converted to True."""
        # GIVEN the string 'True'

        # WHEN we convert it
        result = str_to_bool("True")

        # THEN it returns True
        assert result is True

    def test_lowercase_true_returns_true(self):
        """Test that 'true' is converted to True."""
        # GIVEN the string 'true'

        # WHEN we convert it
        result = str_to_bool("true")

        # THEN it returns True
        assert result is True

    def test_false_string_returns_false(self):
        """Test that 'False' is converted to False."""
        # GIVEN the string 'False'

        # WHEN we convert it
        result = str_to_bool("False")

        # THEN it returns False
        assert result is False

    def test_lowercase_false_returns_false(self):
        """Test that 'false' is converted to False."""
        # GIVEN the string 'false'

        # WHEN we convert it
        result = str_to_bool("false")

        # THEN it returns False
        assert result is False

    def test_invalid_string_raises_value_error(self):
        """Test that an invalid string raises ValueError."""
        # GIVEN an invalid string

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError, match="Cannot convert"):
            str_to_bool("yes")

    def test_empty_string_raises_value_error(self):
        """Test that an empty string raises ValueError."""
        # GIVEN an empty string

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError):
            str_to_bool("")

    def test_return_type_is_bool(self):
        """Test that the return type is always bool."""
        # GIVEN valid inputs

        # WHEN we convert them
        # THEN the return type is bool
        assert isinstance(str_to_bool("True"), bool)
        assert isinstance(str_to_bool("False"), bool)
