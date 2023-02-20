"""IRTransEntity class"""
import logging
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME, ATTRIBUTION
from .api import IRTransCon

_LOGGER: logging.Logger = logging.getLogger(__package__)


class IRTransEntity(CoordinatorEntity):
    """IRTrans Entity"""

    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._state = None
        self.host = self.coordinator.api.data["host"]

    async def async_update(self):
        """Retrieve latest state."""
        self._state = IRTransCon.mycfg["irtrans"]  # await async_fetch_state()

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return self.config_entry.entry_id

    @property
    def device_info(self):
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
