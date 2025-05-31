import json
import datetime
import random
import hashlib
import pytz


class SpeechAgent:
    """Handles tool processing and speech-related agent functionality."""

    async def process_tool_use(self, tool_name, tool_use_content):
        """Return the tool result"""
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

    async def _get_date_and_time(self):
        """Get current date and time in PST timezone."""
        # Get current date in PST timezone
        pst_timezone = pytz.timezone("America/Los_Angeles")
        pst_date = datetime.datetime.now(pst_timezone)
        
        return {
            "formattedTime": pst_date.strftime("%I:%M %p"),
            "date": pst_date.strftime("%Y-%m-%d"),
            "year": pst_date.year,
            "month": pst_date.month,
            "day": pst_date.day,
            "dayOfWeek": pst_date.strftime("%A").upper(),
            "timezone": "PST"
        }

    async def _track_order(self, tool_use_content):
        """Track order status with deterministic fake data."""
        # Extract order ID from toolUseContent
        content = tool_use_content.get("content", {})
        content_data = json.loads(content)
        order_id = content_data.get("orderId", "")
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
        
        # Possible statuses with appropriate weights
        statuses = [
            "Order received", 
            "Processing", 
            "Preparing for shipment",
            "Shipped",
            "In transit", 
            "Out for delivery",
            "Delivered",
            "Delayed"
        ]
        
        weights = [10, 15, 15, 20, 20, 10, 5, 3]
        
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