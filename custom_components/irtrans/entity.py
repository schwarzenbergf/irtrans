"""IRTransEntity class."""

import logging
from typing import Any

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import IRTransCon
from .const import ATTRIBUTION, DEBUG, DOMAIN, NAME

_LOGGER: logging.Logger = logging.getLogger(__package__)


class IRTransDeviceInfoMixin:
    """Shared device_info for all entities backed by an IRTrans device.

    Keyed on the config entry id (not on each entity's own unique_id) so that
    entities across platforms (sensor, infrared, ...) attach to the same
    device instead of each spawning its own.
    """

    config_entry: Any
    coordinator: Any

    @property
    def device_info(self):
        """Special Device Attributes."""
        return {
            "identifiers": {(DOMAIN, self.config_entry.entry_id)},
            "name": NAME,
            "model": "IRTrans Ethernet IRDB (LAN firmware)",
            "manufacturer": "IRTrans GmbH",
            "sw_version": IRTransCon.mycfg["firmware"],
            "configuration_url": "http://" + self.coordinator.api.data["host"],
        }


class IRTransEntity(IRTransDeviceInfoMixin, CoordinatorEntity):
    """IRTrans Entity."""

    def __init__(self, coordinator, config_entry) -> None:
        """Init entity."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._state = None
        self.host = self.coordinator.api.data["host"]

    async def async_update(self):
        """Retrieve latest state."""
        if DEBUG:
            _LOGGER.debug("Entity: retrieve latest state %s:", IRTransCon.mycfg)
        self._state = IRTransCon.mycfg["irtrans"]
        return self._state

    @property
    def should_poll(self) -> bool:
        """Do Polling."""
        return True

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return self.config_entry.entry_id

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "attribution": ATTRIBUTION,
            "id": str(self.coordinator.data.get("id")),
            "integration": DOMAIN,
        }
