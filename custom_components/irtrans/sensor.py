"""Sensor platform for irtrans."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant import config_entries
from homeassistant.helpers import entity_platform

from .const import DEFAULT_NAME, DOMAIN, ICON, SENSOR, SERVICES_YAML, DEBUG
from .entity import IRTransEntity
from .api import IRTransApi

_LOGGER: logging.Logger = logging.getLogger(__package__)

irtrans_entry: config_entries.ConfigEntry = None
PARALLEL_UPDATES = 0


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""

    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_devices([IRTransSensor(coordinator, entry)])

    platform = entity_platform.async_get_current_platform()

    if DEBUG:
        _LOGGER.debug(
            "IRTRANS Sensor platform setup: %s",
            " ".join(IRTransApi.myresp["devices"]),
        )
        _LOGGER.debug("Creating services.yaml ...")

    yaml_file = open(
        "custom_components/" + DEFAULT_NAME + "/services.yaml", "wt", encoding="utf-8"
    )

    for remote in IRTransApi.myresp["devices"]:
        if remote == "hw_version":
            break

        # create services.yaml for this service
        s_yaml = SERVICES_YAML.replace("&remote&", remote)
        c_yaml = "            - "
        cmd_yaml = ""
        commands = IRTransApi.myresp["devices"][remote]
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

    @classmethod
    async def send_irtrans_ir_cmd(cls, remote: str, ir_cmd: str) -> None:
        """Send IR Command to IRTrans (Service Call)"""
        result = await IRTransApi.api_irtrans("SEND", remote, ir_cmd)
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
