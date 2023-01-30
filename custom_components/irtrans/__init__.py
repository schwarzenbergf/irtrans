"""
Custom integration to integrate irtrans with Home Assistant.

For more details about this integration, please refer to
https://github.com/custom-components/irtrans
"""
import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

# from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .api import IRTransCon, init_and_listen
from .const import DOMAIN, PLATFORMS, STARTUP_MESSAGE, DEBUG

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
    # api = IRTransCon(hass, entry.data)
    # await api.get_initial()

    # coordinator = IRTransDataUpdateCoordinator(hass, api)
    # await coordinator.sio_connect()

    coordinator = IRTransDataUpdateCoordinator(hass)
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator
    # api.coordinator = coordinator

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

    if DEBUG:
        _LOGGER.debug("async_setup_entry->")

    return True


class IRTransDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize."""
        if DEBUG:
            _LOGGER.debug("IRTransDataUpdateCoordinator")
        self.platforms = []
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        # self.api = api
        self.entry = hass.config_entries.async_entries(DOMAIN)[0]
        self.host = self.entry.data.get("host")
        self.port = self.entry.data.get("port")
        if DEBUG:
            _LOGGER.debug(
                "hass cfg entry: %s %s:%s", self.entry.data, self.host, self.port
            )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            # Start listening to IR Remote commands
            if IRTransCon.trans_port is None:
                if DEBUG:
                    _LOGGER.debug(
                        "Listener is not running, starting now (DataUpdateCoordinator) ..."
                    )
                await init_and_listen(self.host, self.port)
                await asyncio.sleep(1)
            if DEBUG:
                _LOGGER.debug("async_update_data before irtrans")
            resp = await IRTransCon.api_irtrans("GET", "", "")
            if DEBUG:
                _LOGGER.debug("async_update_data after irtrans: %s", resp)
            if len(resp) == 0:
                raise UpdateFailed() from Exception("Connection Timeout")
            return resp
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
