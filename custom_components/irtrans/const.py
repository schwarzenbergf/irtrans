"""Constants for irtrans."""
# Base component constants
NAME = "IRTrans"
DOMAIN = "irtrans"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.1"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"
ISSUE_URL = "https://github.com/custom-components/irtrans/issues"

# Icons
ICON = "mdi:remote"

# Device classes

# Platforms
SENSOR = "sensor"
PLATFORMS = [SENSOR]  # [BINARY_SENSOR, SENSOR, SWITCH]


# Configuration and options
CONF_ENABLED = "enabled"
CONF_USERNAME = "user"
CONF_PASSWORD = "pass"

# Defaults
DEFAULT_NAME = DOMAIN


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""

SERVICES_YAML = """send_irtrans_ir_command_&remote&:
  name: Send IRTrans IR Command
  description: Send for lgsmarttv Remote an IR command
  target:
    entity_id: sensor.irtrans_sensor
  fields:
    remote:
      name: Remote
      required: true
      selector:
        select:
          options:
            - &remote&
    ir_cmd:
      name: IR Command
      description: the IR Command to send to IRTrans using Remote
      required: true
      example: "vol+"
      selector:
        select:
          options:
&commands&
"""
