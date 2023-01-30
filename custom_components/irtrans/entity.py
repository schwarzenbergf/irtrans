"""IRTransEntity class"""
import logging
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME, ATTRIBUTION
from .api import mycfg

_LOGGER: logging.Logger = logging.getLogger(__package__)


class IRTransEntity(CoordinatorEntity):
    """IRTrans Entity"""

    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._state = None

    async def async_update(self):
        """Retrieve latest state."""
        # await IRTransApi.start_listen2ir(IRTransApi.hass)
        self._state = mycfg["irtrans"]  # await async_fetch_state()

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return self.config_entry.entry_id

    @property
    def device_info(self):
        global mycfg  # pylint: disable = global-statement, invalid-name, global-variable-not-assigned
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": NAME,
            "model": "IRTrans Ethernet IRDB (LAN firmware)",
            "manufacturer": "IRTrans GmbH",
            "hw_version": mycfg["version"][2] + " " + mycfg["version"][3],
        }

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "attribution": ATTRIBUTION,
            "id": str(self.coordinator.data.get("id")),
            "integration": DOMAIN,
        }
