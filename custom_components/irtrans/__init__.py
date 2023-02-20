"""
Custom integration to integrate irtrans with Home Assistant.

For more details about this integration, please refer to
https://github.com/custom-components/irtrans
"""
import asyncio
from datetime import timedelta
import logging
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.template import device_id, device_entities

# from homeassistant.helpers import entity_registry
# from homeassistant.helpers.trigger import TriggerInfo, TriggerData

from homeassistant.const import (
    CONF_ENTITY_ID,
    CONF_TYPE,
)
from .api import IRTransAPI, IRTransCon
from .const import (
    DOMAIN,
    PLATFORMS,
    STARTUP_MESSAGE,
    DEBUG,
    GETVER,
    TIMEOUT,
    NAME,
    SENSOR,
)
from .device_trigger import async_get_triggers, async_attach_trigger

SCAN_INTERVAL = timedelta(seconds=300)

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup(
    hass: HomeAssistant, config: Config
):  # pylint: disable=unused-argument
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""

    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    if DEBUG:
        _LOGGER.debug(
            "->async_setup_entry:Config Entry data (async_setup_entry) %s :", entry.data
        )

    coordinator = IRTransDataUpdateCoordinator(hass, entry)
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator
    # if entry.data.get("host"):
    #     MyVars.host = entry.data["host"]
    # if entry.data.get("port"):
    #     MyVars.port = entry.data["port"]

    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            coordinator.platforms.append(platform)
            hass.async_add_job(
                hass.config_entries.async_forward_entry_setup(entry, platform)
            )

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    my_device_id = device_id(hass, NAME)
    entities = device_entities(hass, my_device_id)
    triggers = await async_get_triggers(hass, my_device_id)

    if DEBUG:
        _LOGGER.debug(
            "async_setup_entry--> %s / %s / %s",
            my_device_id,
            triggers,
            entities[0],
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
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.api = IRTransAPI(hass, entry, self)
        self.api_conn = IRTransCon
        self.entry = entry

        if DEBUG:
            _LOGGER.debug(
                "hass cfg entry(IRTransDataUpdateCoordinator): %s:%s",
                self.api.data["host"],
                self.api.data["port"],
            )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            async with async_timeout.timeout(TIMEOUT):
                # Start listening to IR Remote commands
                if self.api_conn.trans_port is None:
                    if DEBUG:
                        _LOGGER.debug(
                            "Listener is not running, starting now (DataUpdateCoordinator) ..."
                        )
                    transport = (  # pylint: disable = unused-variable
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
                    if len(resp) == 0:
                        raise UpdateFailed() from Exception("Connection Timeout")

                    return resp
                # Listener is already running, just get Version to see if still connected
                self.api_conn.trans_port.write(GETVER.encode())
                if DEBUG:
                    _LOGGER.debug("Get Version msg sent (_async_update_data)")
                await asyncio.sleep(1)
                return self.api_conn.mycfg
        except asyncio.TimeoutError as tout:
            _LOGGER.error("Timeout while refresh IRTrans connection (%s)", tout)
            raise UpdateFailed() from tout
        except Exception as exception:
            _LOGGER.error(
                "Something really wrong happened (_async_update_data)! - %s", exception
            )
            raise UpdateFailed() from exception


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    if DEBUG:
        _LOGGER.debug("async_unload_entry")
    IRTransCon.trans_port.close()
    IRTransCon.trans_port = None
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
