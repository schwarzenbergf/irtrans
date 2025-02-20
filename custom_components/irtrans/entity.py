"""IRTransEntity class."""

import logging

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import IRTransCon
from .const import ATTRIBUTION, DEBUG, DOMAIN, NAME

_LOGGER: logging.Logger = logging.getLogger(__package__)


class IRTransEntity(CoordinatorEntity):
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
    def device_info(self):
        """Special Device Attributes."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": NAME,
            "model": "IRTrans Ethernet IRDB (LAN firmware)",
            "manufacturer": "IRTrans GmbH",
            "sw_version": IRTransCon.mycfg["firmware"],
            "configuration_url": "http://" + self.host,
        }

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "attribution": ATTRIBUTION,
            "id": str(self.coordinator.data.get("id")),
            "integration": DOMAIN,
        }
