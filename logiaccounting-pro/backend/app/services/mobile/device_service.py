"""
Device Registration Service
Manages mobile device registration and tokens
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import uuid4
import logging

from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


class Device:
    """Represents a registered device."""

    def __init__(self, contact_id: str, platform: str, device_token: str):
        self.id = f"dev_{uuid4().hex[:12]}"
        self.contact_id = contact_id
        self.platform = platform  # 'web', 'ios', 'android'
        self.device_token = device_token
        self.device_name = None
        self.device_model = None
        self.os_version = None
        self.app_version = None
        self.push_enabled = True
        self.is_active = True
        self.last_active_at = utc_now()
        self.created_at = utc_now()
        self.updated_at = utc_now()


class DeviceService:
    """Manages device registration."""

    def __init__(self):
        self._devices: Dict[str, Device] = {}

    def register_device(self, contact_id: str, data: Dict) -> Device:
        """Register or update a device."""
        # Check if device already exists by token
        existing = self._find_by_token(data.get("token"))

        if existing:
            # Update existing device
            existing.contact_id = contact_id
            existing.last_active_at = utc_now()
            existing.updated_at = utc_now()
            existing.is_active = True

            if "device_name" in data:
                existing.device_name = data["device_name"]
            if "device_model" in data:
                existing.device_model = data["device_model"]
            if "os_version" in data:
                existing.os_version = data["os_version"]
            if "app_version" in data:
                existing.app_version = data["app_version"]

            logger.info(f"Updated device {existing.id} for contact {contact_id}")
            return existing

        # Create new device
        device = Device(
            contact_id=contact_id,
            platform=data.get("platform", "web"),
            device_token=data.get("token"),
        )
        device.device_name = data.get("device_name")
        device.device_model = data.get("device_model")
        device.os_version = data.get("os_version")
        device.app_version = data.get("app_version")

        self._devices[device.id] = device
        logger.info(f"Registered new device {device.id} for contact {contact_id}")

        return device

    def _find_by_token(self, token: str) -> Optional[Device]:
        """Find device by token."""
        if not token:
            return None
        for device in self._devices.values():
            if device.device_token == token:
                return device
        return None

    def unregister_device(self, device_id: str, contact_id: str) -> bool:
        """Unregister a device."""
        device = self._devices.get(device_id)
        if device and device.contact_id == contact_id:
            device.is_active = False
            device.updated_at = utc_now()
            logger.info(f"Unregistered device {device_id}")
            return True
        return False

    def get_devices(self, contact_id: str) -> List[Dict]:
        """Get all active devices for a contact."""
        devices = [
            d for d in self._devices.values()
            if d.contact_id == contact_id and d.is_active
        ]
        return [self._device_to_dict(d) for d in devices]

    def get_device(self, device_id: str, contact_id: str) -> Optional[Dict]:
        """Get a specific device."""
        device = self._devices.get(device_id)
        if device and device.contact_id == contact_id:
            return self._device_to_dict(device)
        return None

    def update_device(self, device_id: str, contact_id: str, data: Dict) -> Optional[Dict]:
        """Update device settings."""
        device = self._devices.get(device_id)
        if not device or device.contact_id != contact_id:
            return None

        if "device_name" in data:
            device.device_name = data["device_name"]
        if "push_enabled" in data:
            device.push_enabled = data["push_enabled"]

        device.updated_at = utc_now()
        return self._device_to_dict(device)

    def update_activity(self, device_id: str) -> bool:
        """Update device last activity timestamp."""
        device = self._devices.get(device_id)
        if device:
            device.last_active_at = utc_now()
            return True
        return False

    def get_push_tokens(self, contact_id: str) -> List[str]:
        """Get all push tokens for a contact's active devices."""
        devices = [
            d for d in self._devices.values()
            if d.contact_id == contact_id and d.is_active and d.push_enabled and d.device_token
        ]
        return [d.device_token for d in devices]

    def cleanup_inactive_devices(self, days: int = 90):
        """Remove devices inactive for specified days."""
        threshold = utc_now() - timedelta(days=days)
        removed = 0

        for device_id, device in list(self._devices.items()):
            if device.last_active_at < threshold:
                device.is_active = False
                removed += 1

        logger.info(f"Deactivated {removed} inactive devices")
        return removed

    def _device_to_dict(self, device: Device) -> Dict:
        """Convert device to dictionary."""
        return {
            "id": device.id,
            "platform": device.platform,
            "device_name": device.device_name,
            "device_model": device.device_model,
            "os_version": device.os_version,
            "app_version": device.app_version,
            "push_enabled": device.push_enabled,
            "last_active_at": device.last_active_at.isoformat(),
            "created_at": device.created_at.isoformat(),
        }


# Service instance
device_service = DeviceService()
