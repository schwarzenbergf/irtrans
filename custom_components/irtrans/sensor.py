"""Sensor platform for irtrans."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers import entity_platform

# from homeassistant.helpers.template import device_id, device_entities

# from homeassistant.helpers import device_registry as dr

from .const import DEFAULT_NAME, DOMAIN, ICON, SENSOR, SERVICES_YAML, DEBUG
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

        _LOGGER.debug("Creating services.yaml ...")

    yaml_file = open(
        "custom_components/" + DEFAULT_NAME + "/services.yaml", "wt", encoding="utf-8"
    )

    # my_device_id = device_id(hass, NAME)
    # entities = device_entities(hass, my_device_id)

    for remote in IRTransCon.mycfg["devices"]:
        if remote == "firmware":
            break

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

        # This will call Entity.send_irtrans_ir_cmd(remote:ir_cmd)
        platform.async_register_entity_service(
            name="send_irtrans_ir_command_" + remote,
            func="send_irtrans_ir_cmd",
            schema={"remote": str, "ir_cmd": str},
        )
    yaml_file.close()
    if DEBUG:
        _LOGGER.debug("Finished writing services.yaml")


class IRTransSensor(IRTransEntity, SensorEntity):
    """irtrans Sensor class."""

    def __init__(self, hass, coordinator, entry):
        """Initialize the sensor."""
        super().__init__(coordinator, entry)

        # self.coordinator = coordinator
        # self.entry = entry
        self.api = IRTransAPI(hass, entry, coordinator)

    # @classmethod
    async def send_irtrans_ir_cmd(self, remote: str, ir_cmd: str) -> None:
        """Send IR Command to IRTrans (Service Call)"""
        result = await self.api.send_ir_remote_cmd(remote, ir_cmd)
        if DEBUG:
            _LOGGER.debug(
                "IRTRANS IR COMMAND: %s -> %s : %s",
                remote,
                ir_cmd,
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
