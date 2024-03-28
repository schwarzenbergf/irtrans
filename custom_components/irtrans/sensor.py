"""Sensor platform for irtrans."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers import entity_platform

# from homeassistant.helpers.template import device_id, device_entities

# from homeassistant.helpers import device_registry as dr

from .const import DEFAULT_NAME, DOMAIN, ICON, SENSOR, SERVICES_YAML, ICONS_JSON, DEBUG
from .entity import IRTransEntity
from .api import IRTransAPI, IRTransCon

# from .device_trigger import async_get_triggers, async_attach_trigger


_LOGGER: logging.Logger = logging.getLogger(__package__)

PARALLEL_UPDATES = 0


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""

    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_devices([IRTransSensor(hass, coordinator, entry)])

    platform = entity_platform.async_get_current_platform()

    if DEBUG:
        _LOGGER.debug(
            "IRTRANS Sensor platform setup: %s",
            " ".join(IRTransCon.mycfg["devices"]),
        )

        _LOGGER.debug("Creating services.yaml & icons.json...")

    yaml_file = open(
        "custom_components/" + DEFAULT_NAME + "/services.yaml", "wt", encoding="utf-8"
    )
    icons_file = open(
        "custom_components/" + DEFAULT_NAME + "/icons.json", "wt", encoding="utf-8"
    )
    s_icons = "{\n\t\"services\": {\n"
    icons_file.write(s_icons)

    # my_device_id = device_id(hass, NAME)
    # entities = device_entities(hass, my_device_id)

    if DEBUG:
        _LOGGER.debug("Number of Remotes: %i", len(IRTransCon.mycfg["devices"]))

    cnt = len(IRTransCon.mycfg["devices"])    
    for remote in IRTransCon.mycfg["devices"]:
        if remote == "firmware":
            break
        cnt -=1
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
        yaml_file.write(s_yaml)
        # create icons.json file for this service
        s_icons = ICONS_JSON.replace("&remote&", remote)
        if cnt > 0:
            s_icons = s_icons + ",\n"
        icons_file.write(s_icons)

        # This will call Entity.send_irtrans_ir_cmd(remote:ir_cmd)
        platform.async_register_entity_service(
            name="send_irtrans_ir_command_" + remote,
            func="send_irtrans_ir_cmd",
            schema={"remote": str, "ir_cmd": str, "led": str, "bus": str, "mask": int},
        )
    yaml_file.close()
    s_icons = "\n\t}\n}"

    icons_file.write(s_icons)
    icons_file.close()

    if DEBUG:
        _LOGGER.debug("Finished writing services.yaml & icons.json")


class IRTransSensor(IRTransEntity, SensorEntity):
    """irtrans Sensor class."""

    def __init__(self, hass, coordinator, entry):
        """Initialize the sensor."""
        super().__init__(coordinator, entry)

        # self.coordinator = coordinator
        # self.entry = entry
        self.api = IRTransAPI(hass, entry, coordinator)

    # @classmethod
    async def send_irtrans_ir_cmd(self, remote: str, ir_cmd: str, led:str=None, bus:str=None, mask:int=None) -> None:
        """Send IR Command to IRTrans (Service Call)"""
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
        return

    @property
    def should_poll(self):
        return False

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
        return self.coordinator.data.get("devices")

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON
