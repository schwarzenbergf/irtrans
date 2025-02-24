"""Sensor platform for irtrans."""

import logging
from pathlib import Path

import aiofiles

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers import entity_platform

from .api import IRTransAPI, IRTransCon

# from homeassistant.helpers.template import device_id, device_entities
# from homeassistant.helpers import device_registry as dr
from .const import DEBUG, DEFAULT_NAME, DOMAIN, ICON, ICONS_JSON, SENSOR, SERVICES_YAML
from .entity import IRTransEntity

# from .device_trigger import async_get_triggers, async_attach_trigger


_LOGGER: logging.Logger = logging.getLogger(__package__)

PARALLEL_UPDATES = 0


async def async_setup_entry(HomeAssistant, entry, async_add_devices):
    """Do setup sensor platform."""

    coordinator = HomeAssistant.data[DOMAIN][entry.entry_id]

    async_add_devices([IRTransSensor(HomeAssistant, coordinator, entry)])

    platform = entity_platform.async_get_current_platform()

    if DEBUG:
        _LOGGER.debug(
            "IRTRANS Sensor platform setup: %s",
            " ".join(IRTransCon.mycfg["devices"]),
        )

    custom_components_path = HomeAssistant.config.path("custom_components")
    yaml_file_path = Path(custom_components_path) / DEFAULT_NAME / "services.yaml"
    icons_file_path = Path(custom_components_path) / DEFAULT_NAME / "icons.json"

    _LOGGER.debug("Creating services.yaml & icons.json")

    yaml_file = await aiofiles.open(
        yaml_file_path,
        "w",
        encoding="utf-8",
    )
    icons_file = await aiofiles.open(
        icons_file_path,
        "w",
        encoding="utf-8",
    )
    s_icons = '{\n\t"services": {\n'
    await icons_file.write(s_icons)

    # my_device_id = device_id(hass, NAME)
    # entities = device_entities(hass, my_device_id)

    if DEBUG:
        _LOGGER.debug("Number of Remotes: %i", len(IRTransCon.mycfg["devices"]))

    cnt = len(IRTransCon.mycfg["devices"]) - 1
    for remote in IRTransCon.mycfg["devices"]:
        if remote == "last_response":
            break
        cnt -= 1
        # create services.yaml for this service
        s_yaml = SERVICES_YAML.replace("&remote&", remote)
        # s_yaml = s_yaml.replace("&device_id", my_device_id)
        c_yaml = "            - "
        cmd_yaml = ""
        commands = IRTransCon.mycfg["devices"][remote]
        for cmd in commands:
            cmd_yaml = c_yaml + '"' + cmd + '"\n' + cmd_yaml
        s_yaml = s_yaml.replace("&commands&", cmd_yaml)
        # if DEBUG:
        #     _LOGGER.debug("services.yaml: %s", s_yaml)
        await yaml_file.write(s_yaml)
        # create icons.json file for this service
        s_icons = ICONS_JSON.replace("&remote&", remote)
        if cnt > 0:
            s_icons = s_icons + ",\n"
        await icons_file.write(s_icons)

        # This will call Entity.send_irtrans_ir_cmd(remote:ir_cmd)
        platform.async_register_entity_service(
            name="send_irtrans_ir_command_" + remote,
            func="send_irtrans_ir_cmd",
            schema={"remote": str, "ir_cmd": str, "led": str, "bus": str, "mask": int},
        )
    await yaml_file.close()
    s_icons = "\n\t}\n}"

    await icons_file.write(s_icons)
    await icons_file.close()

    if DEBUG:
        _LOGGER.debug("Finished writing services.yaml & icons.json")


class IRTransSensor(IRTransEntity, SensorEntity):
    """irtrans Sensor class."""

    def __init__(self, HomeAssistant, coordinator, entry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)

        # self.coordinator = coordinator
        # self.entry = entry
        self.api = IRTransAPI(HomeAssistant, entry, coordinator)

    # @classmethod
    async def send_irtrans_ir_cmd(
        self,
        remote: str,
        ir_cmd: str,
        led: str | None = None,
        bus: str | None = None,
        mask: int | None = None,
    ) -> None:
        """Send IR Command to IRTrans (Service Call)."""
        result = await self.api.send_ir_remote_cmd(remote, ir_cmd, led, bus, mask)
        if DEBUG:
            _LOGGER.debug(
                "IRTRANS IR COMMAND: %s -> %s , %s, %s, %s: %s",
                remote,
                ir_cmd,
                led,
                bus,
                mask,
                result,
            )

    async def async_update(self):
        """Retrieve latest state."""
        if DEBUG:
            _LOGGER.debug("Sensor: retrieve latest state %s:", IRTransCon.mycfg)
        self._state = IRTransCon.mycfg["irtrans"]
        return self._state

    @property
    def should_poll(self):
        """Should poll."""
        return True

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{DEFAULT_NAME}_{SENSOR}"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return self.coordinator.data.get("irtrans")

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        # Add last response to mycfg["devices"], it will be show up in the attributes of the sensor entity
        attr = self.coordinator.data.get("devices")
        attr.update({"last_response": IRTransCon.mycfg["ircmd"]})
        return attr
        # return self.coordinator.data.get("devices")

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON
