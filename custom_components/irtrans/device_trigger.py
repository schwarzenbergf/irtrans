"""Provides device triggers for IRtrans."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import automation
from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import state as state_trigger

# from homeassistant.components.homeassistant.triggers import (
#     event as event_trigger,
# )
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_EVENT_DATA,
    CONF_PLATFORM,
    CONF_TYPE,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry as er

# from homeassistant.helpers import trigger
from homeassistant.helpers.typing import ConfigType

from .const import DEBUG, DOMAIN

_LOGGER: logging.Logger = logging.getLogger(__package__)

TRIGGER_TYPES = {"remote_pressed"}
INPUTS_EVENTS_SUBTYPES = {"remote", "button"}
CONF_RMT_BUTTON = "button"
CONF_IR_REMOTE = "remote"
# IR_REMOTE = ["lgsmarttv", "denon", "htpc"]
IR_REMOTE = ["first", "second", "third"]
IR_BUTTON = [
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "vol+",
    "vol-",
    "ch+",
    "ch-",
]
CONF_SUBTYPE = "subtype"


TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
        vol.Optional(CONF_EVENT_DATA): str,
        vol.Optional(CONF_IR_REMOTE): str,
        vol.Optional(CONF_RMT_BUTTON): str,
    }
)


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """List device triggers for IRtrans devices."""

    registry = er.async_get(hass)
    triggers = []

    base_trigger = {
        CONF_PLATFORM: "device",
        CONF_DEVICE_ID: device_id,
        CONF_DOMAIN: DOMAIN,
    }

    # Get all the integrations entities for this device
    for entry in er.async_entries_for_device(registry, device_id):
        if entry.platform != DOMAIN:
            continue
        # Add triggers for each entity that belongs to this integration
        triggers.append(
            {
                **base_trigger,
                CONF_ENTITY_ID: entry.entity_id,
                CONF_TYPE: "remote_pressed",
                CONF_EVENT_DATA: {"remote": IR_REMOTE, "button": IR_BUTTON},
            }
        )

        # Write important information to log
        if DEBUG:
            _LOGGER.debug(
                "Triggers(device_trigger): %s, %s, %s",
                entry.platform,
                entry.domain,
                triggers,
            )

    return triggers


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: automation.AutomationTriggerData,  # TriggerActionType,
    trigger_info: automation.AutomationTriggerInfo,  # TriggerInfo
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    # Use the existing state or event triggers from the automation integration.

    if config[CONF_TYPE] == "remote_pressed":
        to_state = "Remote button pressed"
    else:
        to_state = "connetced"

    # event_config = event_trigger.TRIGGER_SCHEMA(
    #     {
    #         event_trigger.CONF_PLATFORM: "event",
    #         event_trigger.CONF_EVENT_TYPE: "irtrans_event",
    #         event_trigger.CONF_EVENT_DATA: {
    #             CONF_ENTITY_ID: config[CONF_ENTITY_ID],
    #             CONF_TYPE: config[CONF_TYPE],
    #             CONF_IR_REMOTE: str,
    #             CONF_RMT_BUTTON: str,
    #         },
    #     }
    # )
    # return await event_trigger.async_attach_trigger(
    #     hass, event_config, action, trigger_info, platform_type="device"
    # )

    state_config = {
        state_trigger.CONF_PLATFORM: "state",
        CONF_ENTITY_ID: config[CONF_ENTITY_ID],
        state_trigger.CONF_TO: to_state,
    }
    state_config = await state_trigger.async_validate_trigger_config(hass, state_config)
    return await state_trigger.async_attach_trigger(
        hass, state_config, action, trigger_info, platform_type="device"
    )
