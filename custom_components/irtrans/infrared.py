"""Infrared emitter platform for irtrans.

Exposes the IRTrans device as a Home Assistant `infrared` emitter entity so
that other integrations (e.g. lg_infrared) can send IR commands through it
without knowing anything about IRTrans's own remote/command database. See
https://developers.home-assistant.io/blog/2026/03/30/infrared-entity-platform/
"""

import logging

from homeassistant.components.infrared import InfraredCommand, InfraredEmitterEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEBUG, DOMAIN
from .entity import IRTransDeviceInfoMixin

_LOGGER: logging.Logger = logging.getLogger(__package__)

PARALLEL_UPDATES = 0

# Pronto/CCF codes must end on a mark+space pair. Protocols such as NEC end
# their raw timings on a lone trailing mark; pad with a nominal trailing gap.
_TRAILING_GAP_US = 40000

# Pronto clock: one frequency word unit = 1 / 4145146 Hz
_PRONTO_REFERENCE_FREQUENCY = 4145146
_PRONTO_DEFAULT_FREQUENCY = 38000


def raw_timings_to_pronto_hex(timings: list[int], modulation: int | None) -> str:
    """Encode raw timings (us, marks > 0, spaces < 0) as a learned Pronto code.

    Same encoding as infrared_protocols' ProntoCommand.from_raw_timings(),
    kept here because Home Assistant pins an infrared-protocols version that
    may not ship the Pronto module yet.
    """
    modulation = modulation or _PRONTO_DEFAULT_FREQUENCY
    time_base = 1000000 / modulation
    words = [
        0x0000,  # learned code
        round(_PRONTO_REFERENCE_FREQUENCY / modulation),  # modulation frequency
        len(timings) // 2,  # burst pairs in the once sequence
        0,  # burst pairs in the repeat sequence
    ]
    for timing in timings:
        duration = timing - 20 if timing > 0 else -timing + 20
        words.append(min(max(round((duration + time_base / 2) / time_base), 1), 0xFFFF))
    return " ".join(f"{word:04x}" for word in words)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the irtrans infrared emitter from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([IRTransEmitterEntity(coordinator, entry)])


class IRTransEmitterEntity(
    IRTransDeviceInfoMixin, CoordinatorEntity, InfraredEmitterEntity
):
    """Infrared emitter entity backed by an IRTrans device."""

    _attr_has_entity_name = True
    _attr_name = "IR emitter"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Init entity."""
        super().__init__(coordinator)
        self.config_entry = config_entry

    @property
    def unique_id(self) -> str:
        """Return a unique ID for this emitter, distinct from the sensor entity."""
        return f"{self.config_entry.entry_id}-emitter"

    async def async_send_command(self, command: InfraredCommand) -> None:
        """Send an IR command through the IRTrans device."""
        timings = command.get_raw_timings()
        if len(timings) % 2:
            timings = [*timings, -_TRAILING_GAP_US]

        pronto_hex = raw_timings_to_pronto_hex(timings, command.modulation)

        if DEBUG:
            _LOGGER.debug("Sending infrared command via IRTrans as CCF: %s", pronto_hex)

        await self.coordinator.api.send_ccf(
            pronto_hex, repeat_count=command.repeat_count
        )
