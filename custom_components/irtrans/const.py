"""Constants for irtrans."""
# Base component constants
NAME = "IRTrans"
DOMAIN = "irtrans"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.1.0"
ATTRIBUTION = ""
ISSUE_URL = "https://github.com/custom-components/irtrans/issues"
DEBUG = True

# Icons
ICON = "mdi:remote"

# Device classes

# Platforms
SENSOR = "sensor"
PLATFORMS = [SENSOR]

# Configuration and options
CONF_ENABLED = "enabled"
CONF_HOST = "nnn.nnn.nnn.nnn"
CONF_PORT = "21000"  # default IRTrans port
GETVER = "Aver\n"  # Get firmware version from IRTrans
TIMEOUT = 10

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
  fields:
    remote:
      name: Remote
      description: &remote&
      required: true
      selector:
        select:
          options:
            - &remote&
    ir_cmd:
      name: IR Command
      description: IR Command to send to &remote&
      required: true
      example: "vol+"
      selector:
        select:
          options:
&commands&
"""
