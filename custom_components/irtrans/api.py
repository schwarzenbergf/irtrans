"""IRTrans API Client."""

import asyncio
import logging
from typing import Any

# from homeassistant.config_entries import ConfigEntry
# from homeassistant.helpers import device_registry as dr
# from homeassistant.helpers import entity_registry as er
# from homeassistant.helpers.template import device_entities, device_id
import homeassistant.helpers.entity_registry as er

# from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import DEBUG, GETVER, REPLY_TIMEOUT, SENSOR

_LOGGER: logging.Logger = logging.getLogger(__package__)


class IRTransCon(asyncio.Protocol):
    """Handle connection to IRTrans."""

    mycfg = {
        "irtrans": "not connected",
        "devices": {},
        "version": "????",
        "firmware": "unkwown",
        "ircmd": "no command sent yet",
    }
    recv_data = None
    trans_port: asyncio.Transport | None = None
    # The request currently waiting for an answer:
    # (expected reply keyword, required prefix of the reply payload, future)
    _waiter: tuple[str, str | None, asyncio.Future] | None = None
    # IRTrans answers one request at a time, so requests are serialized
    _request_lock = asyncio.Lock()
    # `entry_id` is specific to a config entry instance. Capture it from
    # the coordinator instance in `__init__` instead of using the
    # `ConfigEntry` class directly.

    def __init__(self, msg, on_con_lost, coordinator, HomeAssistant) -> None:
        """Init IRTRansCon."""
        self.msg = msg
        self.on_con_lost = on_con_lost
        self.coordinator = coordinator
        self.hass = HomeAssistant
        # coordinator should be the DataUpdateCoordinator instance which
        # holds a reference to the config entry as `entry`.
        self.entry_id = None
        try:
            self.entry_id = getattr(
                getattr(coordinator, "entry", None), "entry_id", None
            )
        except AttributeError:
            # Defensive: if anything goes wrong, leave entry_id as None.
            self.entry_id = None

    def connection_made(self, transport: asyncio.Transport):
        """Write to transport."""
        IRTransCon.trans_port = transport
        transport.write(self.msg.encode())
        if DEBUG:
            _LOGGER.debug("Data sent %s:", self.msg)

    @staticmethod
    async def write_data(transport, data):
        """Write Data to socket."""

        try:
            transport.write(data.encode())
            while transport.get_write_buffer_size() > 0:
                continue
            if DEBUG:
                _LOGGER.debug("Data sent %s: ", data)
        except Exception as exception:  # noqa: BLE001
            if DEBUG:
                _LOGGER.error("Write Data exception! - %s", exception)

    @staticmethod
    async def request(
        msg: str, expected: str, prefix: str | None = None
    ) -> list | None:
        """Send msg and wait for the matching reply (None on timeout).

        Replies that don't match (e.g. late answers to an earlier request)
        are ignored instead of being mistaken for the answer to this one.
        """
        if IRTransCon.trans_port is None:
            _LOGGER.error("Not connected to IRTrans, cannot send %s", msg.strip())
            return None
        async with IRTransCon._request_lock:
            future = asyncio.get_running_loop().create_future()
            IRTransCon._waiter = (expected, prefix, future)
            IRTransCon.recv_data = None
            try:
                await IRTransCon.write_data(IRTransCon.trans_port, msg)
                return await asyncio.wait_for(future, REPLY_TIMEOUT)
            except TimeoutError:
                _LOGGER.error("No answer from IRTrans for %s", msg.strip())
                return None
            finally:
                IRTransCon._waiter = None

    @staticmethod
    def _resolve_waiter(data: list) -> None:
        """Hand a reply to the waiting request if it is the expected one."""
        waiter = IRTransCon._waiter
        if waiter is not None:
            expected, prefix, future = waiter
            if (
                not future.done()
                and expected in data[1]
                and (prefix is None or (len(data) > 2 and data[2].startswith(prefix)))
            ):
                future.set_result(data)
                return
        if DEBUG:
            _LOGGER.debug("Ignoring unrequested/stale reply from IRTrans %s", data)

    def data_received(self, data):
        """Receive data."""
        # Several replies may arrive in one chunk, one per line
        for line in data.decode().splitlines():
            line = line.strip()
            if line:
                self._handle_line(line)

    def _handle_line(self, data):
        """Handle a single reply line from IRTrans."""
        if DEBUG:
            _LOGGER.debug("Data received %s:", data)
        data = data.split(" ", 2)  # split on ' ', but max. 3 parts
        if len(data) < 2:
            return
        if data[0].find("**"):
            self.mycfg["irtrans"] = "connected"
        if data[1] == "RCV_COM":  # IR Remote command received
            _LOGGER.debug("IR Remote command received %s:", data)
            if len(data) > 2:
                self._fire_remote_event(data[2].split(","))
        if data[1] == "VERSION":  # Response to Aver
            IRTransCon.mycfg["version"] = data
            IRTransCon.mycfg["firmware"] = data[2] if len(data) > 2 else "unknown"
            if DEBUG:
                _LOGGER.debug(
                    "Version/Firmware %s/%s:", data, IRTransCon.mycfg["firmware"]
                )
        if data[1] in ("REMOTELIST", "COMMANDLIST") or "RESULT" in data[1]:
            # Response to Agetremotes / Agetcommands / IR send
            if DEBUG:
                _LOGGER.debug("Response to %s request %s:", data[1], data)
            IRTransCon.recv_data = data
            self._resolve_waiter(data)
        self.coordinator.async_set_updated_data(self.mycfg)

    def _fire_remote_event(self, data):
        """Fire irtrans_event for a received IR remote button press."""
        if len(data) < 2:
            return
        entity_registry = er.async_get(self.hass)
        my_device_id = None

        # Prefer matching entities by their `config_entry_id` which links
        # entities to the config entry. This is more reliable than trying
        # to match on `unique_id`.
        for entity in entity_registry.entities.values():
            # _LOGGER.debug("entity --> %s", entity)
            if getattr(entity, "config_entry_id", None) == self.entry_id:
                my_device_id = entity.device_id
                break

        if not my_device_id:
            _LOGGER.error("Device ID could not be determined for the integration")
            return

        # The sensor entity is the one whose state/events represent received
        # IR remote button presses. Other platforms (e.g. infrared emitter)
        # share this device but aren't the right target for this event.
        entities = [
            e.entity_id
            for e in entity_registry.entities.values()
            if e.device_id == my_device_id and e.domain == SENSOR
        ]

        if not entities:
            _LOGGER.error("No sensor entity found for device %s", my_device_id)
            return

        # Fire an event for the sensor entity on the device.
        event_data = {
            "entity_id": entities[0],
            "type": "remote_pressed",
            "remote": data[0],
            "button": data[1],
        }
        self.hass.bus.async_fire("irtrans_event", event_data)

    def connection_lost(self, exc):
        """Tell Connection lost."""
        if DEBUG:
            _LOGGER.debug("The server closed the connection %s", exc)
        self.mycfg["irtrans"] = "disconnected"
        IRTransCon.trans_port = None
        self.on_con_lost.set_result(True)


class IRTransAPI:
    """IRTrans API to send commands."""

    def __init__(self, HomeAssistant, entry, coordinator) -> None:
        """Init IRTrans API."""
        self.hass = HomeAssistant
        self.data = entry.data
        self.coordinator = coordinator
    async def init_and_listen(self, host, port) -> Any:
        """Initialize connection to IRTrans and start listening."""
        # Get a reference to the event loop as we plan to use
        # low-level APIs.
        # low-level APIs.
        loop = asyncio.get_running_loop()
        on_con_lost = loop.create_future()
        _LOGGER.debug("Conneting to %s:%s", host, port)
        (
            IRTransCon.trans_port,
            _,
        ) = await loop.create_connection(
            lambda: IRTransCon(GETVER, on_con_lost, self.coordinator, self.hass),
            host,
            int(port),
        )
        _LOGGER.debug("Listening on %s:%s", host, port)
        return IRTransCon.trans_port

    # @classmethod
    async def get_irtrans_info(self, cmd, res, offset) -> list:
        """Send irTrans command and get result."""

        if DEBUG:
            _LOGGER.debug(
                "Send irTrans command cmd: %s res: %s offset: %i",
                cmd,
                res,
                offset,
            )
        msg = cmd + str(offset) + "\n"
        # The reply payload starts with the requested offset, e.g. "1,6,5,..."
        data = await IRTransCon.request(msg, res, str(offset) + ",")
        if data is None or len(data) < 3:
            return []
        IRTransCon.mycfg["irtrans"] = "connected"
        return data[2].split(",")

    # @staticmethod
    async def send_ir_remote_cmd(
        self,
        remote: str,
        command: str,
        led: str | None = None,
        bus: str | None = None,
        mask: int | None = None,
    ) -> dict:
        """Send IR command for specified remote to IRTrans."""

        rsp = {"ircmd": "success"}
        msg = "Asnd " + remote + "," + command
        if led is not None:
            msg = msg + ",l" + led
        if bus is not None:
            msg = msg + ",b" + bus
        if mask is not None:
            msg = msg + "," + str(mask)
        msg = msg + "\n"
        if DEBUG:
            _LOGGER.debug("Command to send to IRTrans: %s", msg)
        data = await IRTransCon.request(msg, "RESULT")
        if data is not None and len(data) > 0:
            if len(data) > 2 and data[2] == "OK":
                rsp["ircmd"] = "Success sending IR command: " + remote + "->" + command
            else:
                rsp["ircmd"] = (
                    "Error sending IR command: "
                    + remote
                    + "->"
                    + command
                    + " : "
                    + " ".join(data)
                )
                if DEBUG:
                    _LOGGER.debug(
                        "Error sending IR command: %s",
                        " ".join(data),
                    )
        else:
            if DEBUG:
                _LOGGER.error(
                    "No answer from IRTrans on sending IR command: %s / %s",
                    remote,
                    command,
                )
            rsp["ircmd"] = "No answer from IRTrans"

        IRTransCon.mycfg["ircmd"] = rsp
        return rsp

    # @staticmethod
    async def send_ccf(self, ccf_hex: str, repeat_count: int = 0) -> dict:
        """Send a Pronto/CCF hex code to IRTrans.

        NOTE: Asndccf is the only raw-send command confirmed to work over
        IRTrans's TCP protocol (Sndhex/Asndhex return "Not supported" on at
        least some firmware). The exact wire syntax below is our best
        reconstruction from public forum reports, not from IRTrans's own
        protocol reference - verify against your device's documentation
        before relying on this in production.
        """
        rsp = {"ircmd": "success"}
        msg = "Asndccf " + ccf_hex.replace(" ", "") + "\n"
        if DEBUG:
            _LOGGER.debug("CCF command to send to IRTrans: %s", msg)

        for _ in range(repeat_count + 1):
            data = await IRTransCon.request(msg, "RESULT")
            if data is not None and len(data) > 0:
                if len(data) > 2 and data[2] == "OK":
                    rsp["ircmd"] = "Success sending CCF command"
                else:
                    rsp["ircmd"] = "Error sending CCF command: " + " ".join(data)
                    if DEBUG:
                        _LOGGER.debug("Error sending CCF command: %s", " ".join(data))
            else:
                if DEBUG:
                    _LOGGER.error("No answer from IRTrans on sending CCF command")
                rsp["ircmd"] = "No answer from IRTrans"

        IRTransCon.mycfg["ircmd"] = rsp
        return rsp

    # @classmethod
    async def api_irtrans(self) -> dict:
        """IRTrans API handler."""
        try:
            # REMOTELIST reply: offset,total,count,name,... (name at offset first)
            devices = {}
            remotes = await self.get_irtrans_info("Agetremotes ", "REMOTELIST", 0)
            if len(remotes) < 4:
                _LOGGER.error("Failed to get REMOTELIST from IRTrans: %s", remotes)
                return {}
            total = int(remotes[1])
            devices[remotes[3]] = []  # first Remote

            for i in range(1, total):  # get all Remotes from irTrans
                remotes = await self.get_irtrans_info("Agetremotes ", "REMOTELIST", i)
                if len(remotes) < 4:
                    _LOGGER.error(
                        "Failed to get REMOTELIST %i from IRTrans: %s", i, remotes
                    )
                    return {}
                devices[remotes[3]] = []
            # get all IR commands for every Remote (will be sensor attributes)
            # COMMANDLIST reply: offset,total,count,command,...
            for device in devices:
                commands = []
                offset = 0
                while True:
                    resp = await self.get_irtrans_info(
                        "Agetcommands " + device + ",", "COMMANDLIST", offset
                    )
                    if len(resp) < 3:
                        _LOGGER.error(
                            "Failed to get COMMANDLIST for %s from IRTrans: %s",
                            device,
                            resp,
                        )
                        return {}
                    commands.extend(resp[3:])
                    count = int(resp[2])
                    offset = offset + count
                    if count == 0 or offset >= int(resp[1]):
                        break
                devices[device] = commands

            IRTransCon.mycfg["devices"] = devices

        except Exception:
            _LOGGER.exception("Something really wrong happened (api module)!")
            return {}
        return IRTransCon.mycfg
