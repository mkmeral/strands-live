import json
import datetime
import random
import hashlib
import pytz
from typing import Dict, Any, List, Optional

from .tool_handler_base import ToolHandlerBase


class ToolHandler(ToolHandlerBase):
    """
    Default implementation of tool handler with date/time and order tracking tools.
    
    This handler provides:
    - Date and time functionality in PST timezone
    - Order tracking with deterministic fake data
    - Extensible architecture for adding new tools
    """
    
    def _initialize_handler(self) -> None:
        """Initialize the default tool handler."""
        # Set default timezone if not configured
        if 'timezone' not in self.config:
            self.config['timezone'] = 'America/Los_Angeles'
        
        # Set default order statuses if not configured
        if 'order_statuses' not in self.config:
            self.config['order_statuses'] = [
                "Order received", 
                "Processing", 
                "Preparing for shipment",
                "Shipped",
                "In transit", 
                "Out for delivery",
                "Delivered",
                "Delayed"
            ]
        
        # Set default status weights if not configured
        if 'status_weights' not in self.config:
            self.config['status_weights'] = [10, 15, 15, 20, 20, 10, 5, 3]

    async def process_tool_use(self, tool_name: str, tool_use_content: Dict[str, Any]) -> Dict[str, Any]:
        """Process tool use request and return the result."""
        # Validate the request first
        if not await self.validate_tool_request(tool_name, tool_use_content):
            return await self.handle_tool_error(tool_name, ValueError("Invalid tool request"))
        
        try:
            tool = tool_name.lower()
            
            if tool == "getdateandtimetool":
                return await self._get_date_and_time()
            elif tool == "trackordertool":
                return await self._track_order(tool_use_content)
            else:
                return {
                    "error": f"Unknown tool: {tool_name}",
                    "toolName": tool_name
                }
        except Exception as e:
            return await self.handle_tool_error(tool_name, e)

    def get_supported_tools(self) -> List[str]:
        """Get list of supported tools."""
        return ["getDateAndTimeTool", "trackOrderTool"]
    
    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get the schema for a specific tool."""
        schemas = {
            "getdateandtimetool": {
                "name": "getDateAndTimeTool",
                "description": "Get information about the current date and time",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                "returns": {
                    "formattedTime": "string (formatted time)",
                    "date": "string (current date)",
                    "year": "number (current year)",
                    "month": "number (current month)",
                    "day": "number (current day)",
                    "dayOfWeek": "string (day of the week)",
                    "timezone": "string (timezone abbreviation)"
                }
            },
            "trackordertool": {
                "name": "trackOrderTool",
                "description": "Retrieves real-time order tracking information and detailed status updates for customer orders by order ID. Provides estimated delivery dates. Use this tool when customers ask about their order status or delivery timeline.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "orderId": {
                            "type": "string",
                            "description": "The order number or ID to track"
                        },
                        "requestNotifications": {
                            "type": "boolean",
                            "description": "Whether to set up notifications for this order",
                            "default": False
                        }
                    },
                    "required": ["orderId"]
                },
                "returns": {
                    "orderStatus": "string (current status of the order)",
                    "orderNumber": "string (the order number that was tracked)",
                    "estimatedDelivery": "string (optional, estimated delivery date)",
                    "trackingHistory": "array (optional, tracking history)",
                    "notificationStatus": "string (optional, notification setup status)"
                }
            }
        }
        
        return schemas.get(tool_name.lower())

    async def _get_date_and_time(self) -> Dict[str, Any]:
        """Get current date and time in configured timezone."""
        timezone_name = self.get_config('timezone', 'America/Los_Angeles')
        timezone = pytz.timezone(timezone_name)
        current_time = datetime.datetime.now(timezone)
        
        return {
            "formattedTime": current_time.strftime("%I:%M %p"),
            "date": current_time.strftime("%Y-%m-%d"),
            "year": current_time.year,
            "month": current_time.month,
            "day": current_time.day,
            "dayOfWeek": current_time.strftime("%A").upper(),
            "timezone": timezone_name.split('/')[-1]  # Extract timezone abbreviation
        }

    async def _track_order(self, tool_use_content: Dict[str, Any]) -> Dict[str, Any]:
        """Track order status with deterministic fake data."""
        # Extract order ID - handle both old and new formats
        if "content" in tool_use_content:
            # Old format - content contains JSON string
            content = tool_use_content.get("content", {})
            content_data = json.loads(content) if isinstance(content, str) else content
            order_id = content_data.get("orderId", "")
            request_notifications = tool_use_content.get("requestNotifications", False)
        else:
            # New format - direct parameters from Bedrock
            order_id = tool_use_content.get("orderId", "")
            request_notifications = tool_use_content.get("requestNotifications", False)
        
        # Convert order_id to string if it's an integer
        if isinstance(order_id, int):
            order_id = str(order_id)
        
        # Validate order ID format
        if not order_id or not isinstance(order_id, str):
            return {
                "error": "Invalid order ID format",
                "orderStatus": "",
                "estimatedDelivery": "",
                "lastUpdate": ""
            }
        
        # Create deterministic randomness based on order ID
        # This ensures the same order ID always returns the same status
        seed = int(hashlib.md5(order_id.encode(), usedforsecurity=False).hexdigest(), 16) % 10000
        random.seed(seed)
        
        # Get configured statuses and weights
        statuses = self.get_config('order_statuses')
        weights = self.get_config('status_weights')
        
        # Select a status based on the weights
        status = random.choices(statuses, weights=weights, k=1)[0]
        
        # Generate a realistic estimated delivery date
        today = datetime.datetime.now()
        # Handle estimated delivery date based on status
        if status == "Delivered":
            # For delivered items, delivery date is in the past
            delivery_days = -random.randint(0, 3)
            estimated_delivery = (today + datetime.timedelta(days=delivery_days)).strftime("%Y-%m-%d")
        elif status == "Out for delivery":
            # For out for delivery, delivery is today
            estimated_delivery = today.strftime("%Y-%m-%d")
        else:
            # For other statuses, delivery is in the future
            delivery_days = random.randint(1, 10)
            estimated_delivery = (today + datetime.timedelta(days=delivery_days)).strftime("%Y-%m-%d")

        # Handle notification request if enabled
        notification_message = ""
        if request_notifications and status != "Delivered":
            notification_message = f"You will receive notifications for order {order_id}"

        # Return comprehensive tracking information
        tracking_info = {
            "orderStatus": status,
            "orderNumber": order_id,
            "notificationStatus": notification_message
        }

        # Add appropriate fields based on status
        if status == "Delivered":
            tracking_info["deliveredOn"] = estimated_delivery
        elif status == "Out for delivery":
            tracking_info["expectedDelivery"] = "Today"
        else:
            tracking_info["estimatedDelivery"] = estimated_delivery

        # Add location information based on status
        if status == "In transit":
            tracking_info["currentLocation"] = "Distribution Center"
        elif status == "Delivered":
            tracking_info["deliveryLocation"] = "Front Door"
            
        # Add additional info for delayed status
        if status == "Delayed":
            tracking_info["additionalInfo"] = "Weather delays possible"
            
        return tracking_info

    async def validate_tool_request(self, tool_name: str, tool_use_content: Dict[str, Any]) -> bool:
        """Validate tool request with additional checks for specific tools."""
        # First do base validation
        if not await super().validate_tool_request(tool_name, tool_use_content):
            return False
        
        # Additional validation for specific tools
        tool = tool_name.lower()
        
        if tool == "trackordertool":
            # Handle both old and new formats
            if "content" in tool_use_content:
                # Old format - validate content structure
                content = tool_use_content.get("content")
                if not content:
                    return False
                
                try:
                    content_data = json.loads(content) if isinstance(content, str) else content
                    if not content_data.get("orderId"):
                        return False
                except (json.JSONDecodeError, AttributeError):
                    return False
            else:
                # New format - validate direct parameters
                order_id = tool_use_content.get("orderId")
                if not order_id:
                    return False
        
        return True