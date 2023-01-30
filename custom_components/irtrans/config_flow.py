"""Adds config flow for IRTrans."""
import logging
import asyncio
from typing import Any, Dict, Optional
from homeassistant import config_entries

# from homeassistant.core import callback

# from homeassistant.helpers.aiohttp_client import async_create_clientsession
import voluptuous as vol
from homeassistant.helpers.selector import (  # pylint: disable=ungrouped-imports
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import init_and_listen, mycfg
from .const import CONF_HOST, CONF_PORT, NAME, DOMAIN, DEBUG


_LOGGER: logging.Logger = logging.getLogger(__package__)


class IRTransFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for IRTrans."""

    # VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}
        self.entry = None

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle a flow initialized by the user."""
        # global trans_port  # pylint: disable = global-statement, invalid-name, global-variable-not-assigned
        self._errors = {}
        if DEBUG:
            _LOGGER.debug("Config Flow User Input: %s", user_input)
        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
        # if self._async_current_entries():
        #     return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:

            # start tcp listener
            await init_and_listen(user_input["host"], user_input["port"])

            valid = await self._test_host(user_input["host"], user_input["port"])
            if valid:
                return self.async_create_entry(title=NAME, data=user_input)
                # self.entry = self.hass.config_entries.async_entries(DOMAIN)[0]
                # if DEBUG:
                #     _LOGGER.debug("async_step_user - cfg entry: %s", self.entry.data)
                # return result

            self._errors["host"] = "Connect Error"
            return await self._show_config_form()

        user_input = {}
        # Provide defaults for form
        user_input[CONF_HOST] = "nnn.nnn.nnn.nnn"
        user_input[CONF_PORT] = "21000"

        return await self._show_config_form()

    async def _show_config_form(self):
        """Show the configuration form to edit host/port data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("host", default=CONF_HOST): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required("port", default=CONF_PORT): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.NUMBER)
                    ),
                }
            ),
            errors=self._errors,
        )

    async def _test_host(self, host: str, port: str):  # pylint: disable=unused-argument
        """Return true if host/port are valid."""
        global mycfg  # pylint: disable = global-statement, invalid-name, global-variable-not-assigned
        try:
            if DEBUG:
                _LOGGER.debug("User Input: %s : %s", host, port)
            await asyncio.sleep(1)
            if DEBUG:
                _LOGGER.debug("IRTrans Version: %s :", mycfg["version"])
            mycfg["hw_version"] = mycfg["version"][2] + " " + mycfg["version"][3]
            return bool(mycfg["version"][1] == "VERSION")
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error("Cannot connect to - %s : %s", host + ":" + port, exception)
            return False


# class IRTransOptionsFlowHandler(config_entries.OptionsFlow):
#     """IRTrans config flow options handler."""

#     def __init__(self, config_entry):
#         """Initialize HACS options flow."""
#         self.config_entry = config_entry
#         self.options = dict(config_entry.options)

#     async def async_step_init(self, user_input=None):
#         """Manage the options."""
#         return await self.async_step_user(user_input)

#     async def async_step_user(self, user_input=None):
#         """Handle a flow initialized by the user."""
#         if user_input is not None:
#             self.options.update(user_input)
#             return await self._update_options()

#         return self.async_show_form(
#             step_id="user",
#             data_schema=vol.Schema(
#                 {
#                     vol.Required(x, default=self.options.get(x, True)): bool
#                     for x in sorted(PLATFORMS)
#                 }
#             ),
#         )

#     async def _update_options(self):
#         """Update config entry options."""
#         return self.async_create_entry(
#             title=self.config_entry.data.get(CONF_HOST), data=self.options
#         )
