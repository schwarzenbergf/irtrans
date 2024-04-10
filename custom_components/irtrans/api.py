"""Sample API Client."""

import logging
import asyncio
import re

# from homeassistant.helpers import device_registry as dr
# from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.template import device_id, device_entities

# from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DEBUG, GETVER, NAME

_LOGGER: logging.Logger = logging.getLogger(__package__)


class IRTransCon(asyncio.Protocol):
    """Handle connection to IRTrans"""

    mycfg = {
        "irtrans": "not connected",
        "devices": {},
        "version": "????",
        "firmware": "unkwown",
    }
    recv_data = None
    trans_port: asyncio.Transport = None

    def __init__(self, msg, on_con_lost, coordinator, hass):
        self.msg = msg
        self.on_con_lost = on_con_lost
        self.coordinator = coordinator
        self.hass = hass

    def connection_made(self, transport: asyncio.Transport):
        IRTransCon.trans_port = transport
        transport.write(self.msg.encode())
        if DEBUG:
            _LOGGER.debug("Data sent %s:", self.msg)

    @staticmethod
    async def write_data(transport, data):
        """Write Data to socket"""

        try:
            transport.write(data.encode())
            while transport.get_write_buffer_size() > 0:
                continue
            if DEBUG:
                _LOGGER.debug("Data sent %s: ", data)
        except Exception as exception:  # pylint: disable=broad-except
            if DEBUG:
                _LOGGER.error("Write Data exception! - %s", exception)

    def data_received(self, data):
        data = data.decode().strip()
        if DEBUG:
            _LOGGER.debug("Data received %s:", data)
        data = data.split(" ", 2)  # split on ' ', but max. 3 parts
        if data[0].find("**"):
            self.mycfg["irtrans"] = "connected"
        if data[1] == "RCV_COM":  # IR Remote command received
            _LOGGER.debug("IR Remote command received %s:", data)
            data = data[2].split(",")
            entities = device_entities(self.hass, device_id(self.hass, NAME))
            event_data = {
                "entity_id": entities[0],
                "type": "remote_pressed",
                "remote": data[0],
                "button": data[1],
            }
            self.hass.bus.async_fire("irtrans_event", event_data)
            self.coordinator.async_set_updated_data(self.mycfg)

        if data[1] == "VERSION":  # Response to Aver
            IRTransCon.mycfg["version"] = data
            IRTransCon.mycfg["firmware"] = data[2]  # + " " + data[3]
            if DEBUG:
                _LOGGER.debug(
                    "Version/Firmware %s/%s:", data, IRTransCon.mycfg["firmware"]
                )
        if data[1] == "REMOTELIST":  # Response to Agetremotes
            if DEBUG:
                _LOGGER.debug("Response to Agetremotes %s:", data)
            IRTransCon.recv_data = data
        if data[1] == "COMMANDLIST":  # Response to Agetcommands
            if DEBUG:
                _LOGGER.debug("Response to Agetcommands %s:", data)
            IRTransCon.recv_data = data
        if "RESULT" in data[1]:  # Response to IR send
            if DEBUG:
                _LOGGER.debug("Response to IR send %s:", data)
            IRTransCon.recv_data = data

    def connection_lost(self, exc):
        if DEBUG:
            _LOGGER.debug("The server closed the connection %s", exc)
        self.mycfg["irtrans"] = "disconnected"
        IRTransCon.trans_port = None
        self.on_con_lost.set_result(True)


class IRTransAPI:
    """IRTrans API to send commands"""

    def __init__(self, hass, entry, coordinator):
        self.hass = hass
        self.data = entry.data
        self.coordinator = coordinator

    async def init_and_listen(self, host, port) -> any:
        """Initialize connection to IRTrans and start listening"""
        # Get a reference to the event loop as we plan to use
        # low-level APIs.
        loop = asyncio.get_running_loop()
        on_con_lost = loop.create_future()
        _LOGGER.debug("Conneting to %s:%s", host, port)
        # pylint: disable = unused-variable
        (
            IRTransCon.trans_port,
            protocol,
        ) = await loop.create_connection(
            lambda: IRTransCon(GETVER, on_con_lost, self.coordinator, self.hass),
            host,
            int(port),
        )
        _LOGGER.debug("Listening on %s:%s", host, port)
        return IRTransCon.trans_port
        # pylint: enable = unused-variable

    # @classmethod
    async def get_irtrans_info(self, cmd, res, offset) -> list:
        """Send irTrans command and get result"""

        if DEBUG:
            _LOGGER.debug(
                "Send irTrans command cmd: %s res: %s offset: %i",
                cmd,
                res,
                offset,
            )
        msg = cmd + str(offset) + "\n"
        await IRTransCon.write_data(IRTransCon.trans_port, msg)
        await asyncio.sleep(0.3)
        data = IRTransCon.recv_data
        if len(data) > 0:
            if data[1] == res:  # pylint: disable=unsubscriptable-object
                IRTransCon.mycfg["irtrans"] = "connected"
                return data[2].split(",")  # pylint: disable=unsubscriptable-object
            IRTransCon.mycfg["irtrans"] = "Unknown answer from IRTrans: " + data
            if DEBUG:
                _LOGGER.debug(
                    "Unknown answer from IRTrans (irtrans_snd_rcv): %s",
                    data,
                )
        else:
            if DEBUG:
                _LOGGER.error("No answer from IRTrans (irtrans_snd_rcv) %s", data)
        return []

    # @staticmethod
    async def send_ir_remote_cmd(
        self,
        remote: str,
        command: str,
        led: str = None,
        bus: str = None,
        mask: int = None,
    ) -> dict:
        """Send IR command for specified remote to IRTrans"""

        rsp = {"ircmd": "success"}
        msg = "Asnd " + remote + "," + command
        if led is None and bus is None and mask is None:
            msg = msg + "\n"
        else:
            if led is not None:
                msg = msg + ",l" + led
            if bus is not None:
                msg = msg + ",b" + bus
            if mask is not None:
                msg = msg + "," + str(mask)
        msg = msg + "\n"
        if DEBUG:
            _LOGGER.debug("Command to send to IRTrans: %s", msg)
        await IRTransCon.write_data(IRTransCon.trans_port, msg)
        await asyncio.sleep(0.3)
        data = IRTransCon.recv_data
        if len(data) > 0:
            if data[2] == "OK":  # pylint: disable=unsubscriptable-object
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

        IRTransCon.mycfg = rsp
        return rsp

    # @classmethod
    async def api_irtrans(self) -> dict:
        """IRTrans API handler"""
        try:
            # # get first (max.) 3 REMOTES (offset = 0) from irTrans
            devices = {}
            remotes = []
            remotes = await self.get_irtrans_info("Agetremotes ", "REMOTELIST", 0)
            if len(remotes) == 0:
                return {}
            last = int(remotes[1]) - 1
            re.sub(
                r"\s", "_", remotes[3]
            )  # Fix: Add 'r' prefix to treat the string as a raw string
            devices[remotes[3]] = []  # first Remote

            i = 0
            while i < last:  # get all Remotes from irTrans
                i = i + 1
                remotes = await self.get_irtrans_info("Agetremotes ", "REMOTELIST", i)
                re.sub(
                    r"\s", "_", remotes[3]
                )  # Fix: Add 'r' prefix to treat the string as a raw string
                devices[remotes[3]] = []
            # get all IR commands for every Remote (will be sensor attributes)
            for device in devices:
                offset = 0
                resp = await self.get_irtrans_info(
                    "Agetcommands " + device + ",", "COMMANDLIST", offset
                )
                if len(resp) == 0:
                    return
                commands = resp[3:]
                offset = offset + int(resp[2])
                while offset < int(resp[1]):
                    resp = await self.get_irtrans_info(
                        "Agetcommands " + device + ",", "COMMANDLIST", offset
                    )
                    offset = offset + int(resp[2])
                    commands.extend(resp[3:])
                devices[device] = commands

            IRTransCon.mycfg["devices"] = devices

            return IRTransCon.mycfg

        except Exception as exception:  # pylint: disable=broad-except
            if DEBUG:
                _LOGGER.error(
                    "Something really wrong happened (api module)! - %s", exception
                )
