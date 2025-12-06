"""Custom integration to integrate irtrans with Home Assistant.

For more details about this integration, please refer to
https://github.com/custom-components/irtrans
"""

import asyncio
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core_config import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
import homeassistant.helpers.entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import IRTransAPI, IRTransCon
from .const import DEBUG, DOMAIN, GETVER, PLATFORMS, STARTUP_MESSAGE, TIMEOUT
from .device_trigger import async_get_triggers

# from asyncio import timeout
# from homeassistant.helpers import entity_registry
# from homeassistant.helpers.trigger import TriggerInfo, TriggerData
# from homeassistant.helpers.template import device_entities, device_id

SCAN_INTERVAL = timedelta(seconds=300)

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup(hass: HomeAssistant, config: Config):  # pylint: disable=unused-argument
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""

    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    if DEBUG:
        _LOGGER.debug(
            "->async_setup_entry:Config Entry data (async_setup_entry) %s :", entry.data
        )

    coordinator = IRTransDataUpdateCoordinator(hass, entry)
    # await coordinator.async_config_entry_first_refresh()
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator
    # if entry.data.get("host"):
    #     MyVars.host = entry.data["host"]
    # if entry.data.get("port"):
    #     MyVars.port = entry.data["port"]

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # config_entry = hass.config_entries.async_entries(DOMAIN)[0]

    # my_device_id = device_id(hass, NAME)
    #  entities = device_entities(hass, my_device_id)

    # _LOGGER.debug(
    #     "entry --> %s ",
    #     entry,
    # )

    entity_registry = er.async_get(hass)
    my_device_id = None
    for entity in entity_registry.entities.values():
        # _LOGGER.debug(
        #     "entity --> %s ",
        #     entity,
        # )
        if (
            entity.unique_id == entry.entry_id
        ):  # Replace with appropriate matching logic
            my_device_id = entity.device_id
            break

    if not my_device_id:
        _LOGGER.error("Device ID could not be determined for the integration")
        return False

    entities = [
        entity.entity_id
        for entity in entity_registry.entities.values()
        if entity.device_id == my_device_id
    ]
    triggers = await async_get_triggers(hass, my_device_id)

    if DEBUG:
        _LOGGER.debug(
            "async_setup_entry--> %s / %s / %s",
            my_device_id,
            triggers,
            entities,
        )
    # Tr_Info: TriggerInfo = (DOMAIN, "irtrans_event", True, None, None)

    # await async_attach_trigger(
    #     hass,
    #     {CONF_ENTITY_ID: "sensor.irtrans_sensor", CONF_TYPE: "remote_pressed"},
    #     "call-service",
    #     Tr_Info,
    # )

    return True


class IRTransDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        """Initialize."""
        if DEBUG:
            _LOGGER.debug("IRTransDataUpdateCoordinator")
        self.platforms = []
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=SCAN_INTERVAL,
            always_update=True,
        )
        self.api = IRTransAPI(hass, entry, self)
        self.api_conn = IRTransCon
        self.entry = entry
        self._device = None

        if DEBUG:
            _LOGGER.debug(
                "hass cfg entry(IRTransDataUpdateCoordinator): %s:%s",
                self.api.data["host"],
                self.api.data["port"],
            )

    async def _async_update_data(self):
        """Update data via library."""
        if DEBUG:
            _LOGGER.debug("--- _async_update_data called --- ")
        try:
            async with asyncio.timeout(TIMEOUT):
                # Start listening to IR Remote commands
                if self.api_conn.trans_port is None:
                    if DEBUG:
                        _LOGGER.debug(
                            "Listener is not running, starting now (DataUpdateCoordinator) ... "
                        )
                    transport = (  # pylint: disable = unused-variable  # noqa: F841
                        await self.api.init_and_listen(
                            self.api.data["host"], self.api.data["port"]
                        )
                    )
                    await asyncio.sleep(1)
                    if DEBUG:
                        _LOGGER.debug("async_update_data before irtrans")
                    resp = await self.api.api_irtrans()
                    if DEBUG:
                        _LOGGER.debug("async_update_data after irtrans: %s", resp)

                # Listener is already running, just get Version to see if still connected
                if self.api_conn.trans_port is not None:
                    self.api_conn.trans_port.write(GETVER.encode())
                    if DEBUG:
                        _LOGGER.debug("Get Version msg sent (_async_update_data)")
                    await asyncio.sleep(1)
                return self.api_conn.mycfg

            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
        except Exception as exception:
            _LOGGER.error(
                "Something really wrong happened (_async_update_data)! - %s", exception
            )
            raise UpdateFailed from exception


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    if DEBUG:
        _LOGGER.debug("--- async_unload_entry called ---")
    if IRTransCon.trans_port is not None:
        IRTransCon.trans_port.close()
    IRTransCon.trans_port = None

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    hass.data[DOMAIN].pop(entry.entry_id)

    if DEBUG:
        _LOGGER.debug("async_unload_entry->unloaded: %s ", unloaded)
        _LOGGER.debug("async_unload_entry->hass.data: %s ", hass.data[DOMAIN])
    if DEBUG:
        _LOGGER.debug("async_unload_entry->hass.data: %s ", hass.data[DOMAIN])

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    if DEBUG:
        _LOGGER.debug("--- async_reload_entry called ---")
    await async_setup_entry(hass, entry)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    return {
        "entry_data": entry.data,
        "data": entry.runtime_data.data,
    }
