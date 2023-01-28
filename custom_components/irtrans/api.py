"""Sample API Client."""
import logging
import asyncio

from homeassistant.core import HomeAssistant

# from homeassistant.helpers.event import async_call_later
# from homeassistant.config_entries import ConfigEntry as entry
# from typing import Optional  # pylint: disable=unused-argument disable=unused-import
# import async_timeout

from .const import DEBUG

TIMEOUT = 10

_LOGGER: logging.Logger = logging.getLogger(__package__)


class IRTransCon(asyncio.Protocol):
    """Handle connection to IRTrans"""

    def __init__(self, msg, on_con_lost):
        self.msg = msg
        self.on_con_lost = on_con_lost

    def connection_made(self, transport):
        transport.write(self.msg.encode())
        _LOGGER.debug("Data sent %s:", self.msg)

    @classmethod
    async def write_data(cls, transport, data):
        """Write Data to socket"""
        transport.write(data.encode())
        _LOGGER.debug("Data sent %s:", data)

    @classmethod
    def data_received(cls, data):
        data = data.decode()
        _LOGGER.debug("Data received %s:", data)
        data = data.split()
        if data[1] == "RCV_COM":  # IR Remote command received
            IRTransApi.process_ir_cmd(data)
        if data[1] == "VERSION":  # Response to Aver
            IRTransApi.process_version(data)
        if data[1] == "REMOTELIST":  # Response to Agetremotes
            IRTransApi.process_getremotes(data)
        if data[1] == "COMMANDLIST":  # Response to Agetcommands
            IRTransApi.process_getcommands(data)
        if "RESULT" in data[1]:  # Response to IR send
            IRTransApi.process_send_resp(data)

    def connection_lost(self, exc):
        _LOGGER.debug("The server closed the connection")
        self.on_con_lost.set_result(True)


class IRTransApi:
    """API Client Class for IRTrans"""

    myresp = {"irtrans": "not connected", "devices": {}, "hw_version": "unkwown"}
    version: str = "xxx"
    host = None
    port = None
    transport = None
    protocol = None
    recv_data = None
    recv_ircmd = None
    # streamreader = None
    # streamwriter = None
    coordinator = None
    hass: HomeAssistant = None

    def __init__(self):
        """Initialize."""
        self.getver = "Aver\n"  # IRTrans command to get firmware version
        self._available = False

    async def init_and_listen(self, host, port):
        """Initialize connection to IRTrans and start listening"""
        # Get a reference to the event loop as we plan to use
        # low-level APIs.
        loop = asyncio.get_running_loop()
        on_con_lost = loop.create_future()
        IRTransApi.transport, IRTransApi.protocol = await loop.create_connection(
            lambda: IRTransCon(self.getver, on_con_lost), host, int(port)
        )
        _LOGGER.debug("Listening on %s:%s", host, port)

    @classmethod
    def process_ir_cmd(cls, data: list):
        """IR Command received"""
        _LOGGER.debug("IR Remote command received %s:", data)
        cls.recv_ircmd = data

    @classmethod
    def process_version(cls, data: list):
        """Response to Aver received"""
        _LOGGER.debug("Response to Aver %s:", data)
        cls.version = data

    @classmethod
    def process_getremotes(cls, data: list):
        """Response to Agetremotes received"""
        _LOGGER.debug("Response to Agetremotes %s:", data)
        cls.recv_data = data

    @classmethod
    def process_getcommands(cls, data: list):
        """Response to Agetcommands received"""
        _LOGGER.debug("Response to Agetcommands %s:", data)
        cls.recv_data = data

    @classmethod
    def process_send_resp(cls, data: list):
        """Response to IR send received"""
        _LOGGER.debug("Response to IR send %s:", data)
        cls.recv_data = data

    # @classmethod
    async def irtrans_snd_rcv_async(self, cmd, res, offset) -> list:
        """Send irTrans command and get result"""
        if DEBUG:
            _LOGGER.debug(
                "Send irTrans command cmd: %s res: %s offset: %i",
                cmd,
                res,
                offset,
            )
        msg = cmd + str(offset) + "\n"
        await IRTransCon.write_data(IRTransApi.transport, msg)
        # self.writer.write(msg)
        # await self.writer.drain()
        # data = await self.reader.readline()
        await asyncio.sleep(0.3)
        data = IRTransApi.recv_data
        if len(data) > 0:
            # data = data.split()
            if data[1] == res:
                self.myresp["irtrans"] = "connected"
                return data[2].split(",")
            self.myresp["irtrans"] = "Unknown answer from IRTrans: " + data
            if DEBUG:
                _LOGGER.debug(
                    "Unknown answer from IRTrans (irtrans_snd_rcv): %s",
                    data,
                )
        else:
            _LOGGER.error("No answer from IRTrans (irtrans_snd_rcv) %s", data)
        return []

    # @classmethod
    async def irtrans_snd_ir_command_async(self, remote: str, command: str) -> dict:
        """Send IR command for specified remote to IRTrans"""

        rsp = {"ircmd": "success"}
        msg = "Asnd " + remote + "," + command + "\n"
        if DEBUG:
            _LOGGER.debug("Command to send to IRTrans: %s", msg)
        await IRTransCon.write_data(IRTransApi.transport, msg)
        await asyncio.sleep(0.3)
        data = IRTransApi.recv_data
        if len(data) > 0:
            if data[2] == "OK":
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
            _LOGGER.error(
                "No answer from IRTrans on sending IR command: %s / %s",
                remote,
                command,
            )
            rsp["ircmd"] = "No answer from IRTrans"
        return rsp

    @classmethod
    async def api_irtrans(cls, mode: str, remote: str, command: str) -> dict:
        """IRTrans API handler"""
        if DEBUG:
            _LOGGER.debug(
                "IRTRANS IR COMMAND(api_irtrans): %s : %s -> %s",
                mode,
                remote,
                command,
            )
        try:
            # if cls.task is not None:
            #     if DEBUG:
            #         _LOGGER.debug(
            #             "Restarting IRTrans socket(api_irtrans) - cancel task"
            #         )
            #     cls.task.cancel()
            #     cls.task = None
            #     cls.streamwriter.close()
            #     await cls.streamwriter.wait_closed()
            #     if DEBUG:
            #         _LOGGER.debug(
            #             "Restarting IRTrans socket(api_irtrans) - writer closed"
            #         )
            #     await cls.irtrans_open_connection()
            #     if DEBUG:
            #         _LOGGER.debug(
            #             "Restarting IRTrans socket(api_irtrans) - opened Connection"
            #         )
            if mode == "GET":
                # # get first (max.) 3 REMOTES (offset = 0) from irTrans
                devices = {}
                remotes = []
                remotes = await cls.irtrans_snd_rcv_async(
                    cls, "Agetremotes ", "REMOTELIST", 0
                )
                if len(remotes) == 0:
                    return {}
                last = int(remotes[1]) - 1
                devices[remotes[3]] = []  # first Remote

                i = 0
                while i < last:  # get all Remotes from irTrans
                    i = i + 1
                    remotes = await cls.irtrans_snd_rcv_async(
                        cls, "Agetremotes ", "REMOTELIST", i
                    )
                    devices[remotes[3]] = []
                # get all IR commands for every Remote (will be sensor attributes)
                for device in devices:
                    offset = 0
                    resp = await cls.irtrans_snd_rcv_async(
                        cls, "Agetcommands " + device + ",", "COMMANDLIST", offset
                    )
                    if len(resp) == 0:
                        return
                    commands = resp[3:]
                    offset = offset + int(resp[2])
                    while offset < int(resp[1]):
                        resp = await cls.irtrans_snd_rcv_async(
                            cls, "Agetcommands " + device + ",", "COMMANDLIST", offset
                        )
                        offset = offset + int(resp[2])
                        commands.extend(resp[3:])
                    devices[device] = commands

                hw_ver = IRTransApi.version
                devices["hw_version"] = hw_ver[2] + " " + hw_ver[3]

                cls.myresp["devices"] = devices
            if mode == "SEND":
                cls.myresp = await cls.irtrans_snd_ir_command_async(
                    cls, remote, command
                )
            return cls.myresp

        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error(
                "Something really wrong happened (api module)! - %s", exception
            )
