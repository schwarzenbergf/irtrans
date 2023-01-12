"""Sensor platform for irtrans."""
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers import entity_platform
from .const import DEFAULT_NAME, DOMAIN, ICON, SENSOR, SERVICES_YAML
from .entity import IRTransEntity
from .api import IRTransApiClient

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices([IRTransSensor(coordinator, entry)])

    platform = entity_platform.async_get_current_platform()

    _LOGGER.debug(
        "IRTRANS Sensor platform setup %s", " ".join(IRTransApiClient.myresp["devices"])
    )
    yaml_file = open(
        "custom_components/" + DEFAULT_NAME + "/services.yaml", "wt", encoding="utf-8"
    )
    for remote in IRTransApiClient.myresp["devices"]:
        # create services.yaml for this service
        s_yaml = SERVICES_YAML.replace("&remote&", remote)
        c_yaml = "            - "
        cmd_yaml = ""
        commands = IRTransApiClient.myresp["devices"][remote]
        for cmd in commands:
            cmd_yaml = c_yaml + '"' + cmd + '"\n' + cmd_yaml
        s_yaml = s_yaml.replace("&commands&", cmd_yaml)
        _LOGGER.debug("services.yaml: %s", s_yaml)
        yaml_file.write(s_yaml)

        # This will call Entity.send_irtrans_ir_cmd(remote:ir_cmd)
        platform.async_register_entity_service(
            name="send_irtrans_ir_command_" + remote,
            func="send_irtrans_ir_cmd",
            schema={"remote": str, "ir_cmd": str},
        )
    yaml_file.close()


class IRTransSensor(IRTransEntity, SensorEntity):
    """irtrans Sensor class."""

    async def send_irtrans_ir_cmd(self, remote: str, ir_cmd: str) -> None:
        """Send IR Command to IRTrans"""
        irapi = IRTransApiClient()
        result = await IRTransApiClient.async_snd_irtrans_data(
            irapi,
            remote,
            ir_cmd,
        )
        _LOGGER.debug(
            "IRTRANS IR COMMAND: %s -> %s : %s",
            remote,
            ir_cmd,
            result,
        )

        return

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
