from src.models import ModelType


class TestModelType:
    """Tests for the ModelType pseudo-enum."""

    def test_order_value(self):
        """Test that ORDER has the expected value."""
        # GIVEN the ModelType enum

        # WHEN we access the ORDER member
        value = ModelType.ORDER

        # THEN the value matches
        assert value == "Order"

    def test_pin_value(self):
        """Test that PIN has the expected value."""
        # GIVEN the ModelType enum

        # WHEN we access the PIN member
        value = ModelType.PIN

        # THEN the value matches
        assert value == "Pin"

    def test_iteration_returns_all_members(self):
        """Test that iterating over ModelType yields all members."""
        # GIVEN the ModelType enum

        # WHEN we collect all values via iteration
        values = list(ModelType)

        # THEN both Order and Pin members are present
        assert "Order" in values
        assert "Pin" in values
        assert len(values) == 2
