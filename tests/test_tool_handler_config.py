import json

import pytest

from strands_live.tool_handler import ToolHandler


class TestToolHandlerConfiguration:
    """Test cases for ToolHandler configuration management."""

    def test_default_configuration(self):
        """Test that default configuration is properly set."""
        handler = ToolHandler()

        # Test default timezone
        assert handler.get_config("timezone") == "America/Los_Angeles"

        # Test default order statuses
        default_statuses = handler.get_config("order_statuses")
        expected_statuses = [
            "Order received",
            "Processing",
            "Preparing for shipment",
            "Shipped",
            "In transit",
            "Out for delivery",
            "Delivered",
            "Delayed",
        ]
        assert default_statuses == expected_statuses

        # Test default status weights
        default_weights = handler.get_config("status_weights")
        expected_weights = [10, 15, 15, 20, 20, 10, 5, 3]
        assert default_weights == expected_weights

    def test_custom_configuration_override(self):
        """Test that custom configuration properly overrides defaults."""
        custom_config = {
            "timezone": "Europe/London",
            "order_statuses": ["Processing", "Shipped", "Delivered"],
            "status_weights": [30, 40, 30],
            "custom_key": "custom_value",
        }

        handler = ToolHandler(custom_config)

        # Test that custom values override defaults
        assert handler.get_config("timezone") == "Europe/London"
        assert handler.get_config("order_statuses") == [
            "Processing",
            "Shipped",
            "Delivered",
        ]
        assert handler.get_config("status_weights") == [30, 40, 30]
        assert handler.get_config("custom_key") == "custom_value"

    def test_partial_configuration_override(self):
        """Test that partial configuration works correctly."""
        # Only override timezone, keep other defaults
        custom_config = {"timezone": "Asia/Tokyo"}

        handler = ToolHandler(custom_config)

        # Custom config should be used
        assert handler.get_config("timezone") == "Asia/Tokyo"

        # Defaults should still be present for other keys
        assert len(handler.get_config("order_statuses")) == 8
        assert len(handler.get_config("status_weights")) == 8

    def test_configuration_modification_after_init(self):
        """Test that configuration can be modified after initialization."""
        handler = ToolHandler()

        # Modify configuration after init
        handler.set_config("timezone", "UTC")
        handler.set_config("new_key", "new_value")

        # Verify changes
        assert handler.get_config("timezone") == "UTC"
        assert handler.get_config("new_key") == "new_value"

    @pytest.mark.asyncio
    async def test_timezone_configuration_impact(self):
        """Test that timezone configuration affects date/time tool output."""
        timezones = [
            ("America/New_York", "New_York"),
            ("Europe/London", "London"),
            ("Asia/Tokyo", "Tokyo"),
            ("Australia/Sydney", "Sydney"),
        ]

        for timezone_full, timezone_short in timezones:
            handler = ToolHandler({"timezone": timezone_full})
            result = await handler._get_date_and_time()

            assert result["timezone"] == timezone_short

    @pytest.mark.asyncio
    async def test_order_status_configuration_impact(self):
        """Test that order status configuration affects order tracking."""
        custom_statuses = ["Custom Status A", "Custom Status B", "Custom Status C"]
        custom_weights = [33, 33, 34]

        handler = ToolHandler(
            {"order_statuses": custom_statuses, "status_weights": custom_weights}
        )

        # Test multiple order IDs to ensure all custom statuses can be returned
        order_ids = [f"TEST{i:03d}" for i in range(20)]
        returned_statuses = set()

        for order_id in order_ids:
            tool_use_content = {
                "content": json.dumps({"orderId": order_id}),
                "requestNotifications": False,
            }

            result = await handler._track_order(tool_use_content)
            returned_statuses.add(result["orderStatus"])

        # Should only return custom statuses
        for status in returned_statuses:
            assert status in custom_statuses

    def test_configuration_validation(self):
        """Test configuration validation and error handling."""
        # Test with mismatched status/weight lengths
        mismatched_config = {
            "order_statuses": ["Status1", "Status2"],
            "status_weights": [50, 30, 20],  # More weights than statuses
        }

        # Should still work but might have unexpected behavior
        handler = ToolHandler(mismatched_config)
        assert handler.get_config("order_statuses") == ["Status1", "Status2"]
        assert handler.get_config("status_weights") == [50, 30, 20]

    def test_configuration_data_types(self):
        """Test configuration with various data types."""
        config = {
            "string_value": "test_string",
            "int_value": 42,
            "float_value": 3.14,
            "bool_value": True,
            "list_value": [1, 2, 3],
            "dict_value": {"nested": "value"},
        }

        handler = ToolHandler(config)

        # All data types should be preserved
        assert handler.get_config("string_value") == "test_string"
        assert handler.get_config("int_value") == 42
        assert handler.get_config("float_value") == 3.14
        assert handler.get_config("bool_value") is True
        assert handler.get_config("list_value") == [1, 2, 3]
        assert handler.get_config("dict_value") == {"nested": "value"}

    def test_configuration_default_values(self):
        """Test configuration getter with default values."""
        handler = ToolHandler()

        # Test existing keys
        assert handler.get_config("timezone") == "America/Los_Angeles"

        # Test non-existing keys with defaults
        assert handler.get_config("nonexistent_key", "default_value") == "default_value"
        assert handler.get_config("another_key", 42) == 42
        assert handler.get_config("bool_key", True) is True

        # Test non-existing keys without defaults (should return None)
        assert handler.get_config("nonexistent_key") is None

    def test_configuration_immutability_between_instances(self):
        """Test that configuration changes don't affect other instances."""
        config1 = {"timezone": "America/New_York"}
        config2 = {"timezone": "Europe/London"}

        handler1 = ToolHandler(config1)
        handler2 = ToolHandler(config2)

        # Modify config in handler1
        handler1.set_config("timezone", "Asia/Tokyo")
        handler1.set_config("new_key", "value1")

        # handler2 should be unaffected
        assert handler2.get_config("timezone") == "Europe/London"
        assert handler2.get_config("new_key") is None

    def test_handler_info_includes_config(self):
        """Test that handler info includes configuration keys."""
        custom_config = {
            "timezone": "UTC",
            "custom_key1": "value1",
            "custom_key2": "value2",
        }

        handler = ToolHandler(custom_config)
        info = handler.get_handler_info()

        # Should include all config keys
        config_keys = set(info["config_keys"])
        expected_keys = {
            "timezone",
            "order_statuses",
            "status_weights",
            "custom_key1",
            "custom_key2",
        }

        assert expected_keys.issubset(config_keys)

    @pytest.mark.asyncio
    async def test_configuration_persistence_during_execution(self):
        """Test that configuration values persist during tool execution."""
        handler = ToolHandler({"timezone": "Europe/Paris"})

        # Execute multiple tools
        result1 = await handler._get_date_and_time()

        # Change configuration
        handler.set_config("timezone", "Asia/Seoul")

        # Execute tool again
        result2 = await handler._get_date_and_time()

        # Results should reflect the configuration changes
        assert result1["timezone"] == "Paris"
        assert result2["timezone"] == "Seoul"

    def test_config_keys_are_strings(self):
        """Test that configuration keys are handled as strings."""
        # Test with various key types
        handler = ToolHandler()

        # Set config with different key types
        handler.set_config("string_key", "value1")
        handler.set_config(123, "value2")  # Numeric key

        # String keys should work normally
        assert handler.get_config("string_key") == "value1"

        # Numeric keys should also work (converted to string internally if needed)
        assert handler.get_config(123) == "value2"

    @pytest.mark.asyncio
    async def test_empty_configuration(self):
        """Test behavior with empty configuration."""
        handler = ToolHandler({})

        # Should still use defaults
        assert handler.get_config("timezone") == "America/Los_Angeles"
        assert len(handler.get_config("order_statuses")) == 8

        # Tools should still work
        result = await handler._get_date_and_time()
        assert "timezone" in result
