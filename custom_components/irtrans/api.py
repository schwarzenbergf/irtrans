"""Sample API Client."""
import logging
import asyncio

# from homeassistant import config_entries as cfg
# from homeassistant.core import HomeAssistant

# import async_timeout

from .const import DEBUG, GETVER

TIMEOUT = 10

_LOGGER: logging.Logger = logging.getLogger(__package__)
# entries = hoass.config_entries.async_entries(DOMAIN)
# _LOGGER.debug("Config Entries for %s: %s:", DOMAIN, entries)


# pylint: disable = invalid-name
mycfg = {
    "irtrans": "not connected",
    "devices": {},
    "version": "????",
    "hw_version": "unkwown",
}
# IRTrans command to get firmware version

trans_port = None
# protocol = None
recv_data = None
recv_ircmd = None
# pylint: enable = invalid-name


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
        while transport.get_write_buffer_size() > 0:
            continue
        _LOGGER.debug("Data sent %s:", data)

    # @classmethod
    def data_received(self, data):
        global mycfg  # pylint: disable = global-statement, invalid-name, global-variable-not-assigned
        global recv_ircmd  # pylint: disable = global-statement, invalid-name
        global recv_data  # pylint: disable = global-statement, invalid-name
        data = data.decode()
        _LOGGER.debug("Data received %s:", data)
        data = data.split()
        if data[1] == "RCV_COM":  # IR Remote command received
            _LOGGER.debug("IR Remote command received %s:", data)
            recv_ircmd = data
        if data[1] == "VERSION":  # Response to Aver
            _LOGGER.debug("Response to Aver %s:", data)
            mycfg["version"] = data
        if data[1] == "REMOTELIST":  # Response to Agetremotes
            _LOGGER.debug("Response to Agetremotes %s:", data)
            recv_data = data
        if data[1] == "COMMANDLIST":  # Response to Agetcommands
            _LOGGER.debug("Response to Agetcommands %s:", data)
            recv_data = data
        if "RESULT" in data[1]:  # Response to IR send
            _LOGGER.debug("Response to IR send %s:", data)
            recv_data = data

    def connection_lost(self, exc):
        _LOGGER.debug("The server closed the connection %s", exc)
        self.on_con_lost.set_result(True)


async def init_and_listen(host, port):
    """Initialize connection to IRTrans and start listening"""
    global trans_port  # pylint: disable = global-statement, invalid-name
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()
    on_con_lost = loop.create_future()
    _LOGGER.debug("Conneting to %s:%s", host, port)
    # pylint: disable = unused-variable
    (trans_port, protocol,) = await loop.create_connection(
        lambda: IRTransCon(GETVER, on_con_lost), host, int(port)
    )
    _LOGGER.debug("Listening on %s:%s", host, port)
    return
    # pylint: enable = unused-variable


class IRTransApi:
    """API Client Class for IRTrans"""

    def __init__(self):
        """Initialize."""
        self._available = False

    # @classmethod
    async def irtrans_snd_rcv_async(self, cmd, res, offset) -> list:
        """Send irTrans command and get result"""
        global mycfg  # pylint: disable = global-statement, invalid-name, global-variable-not-assigned
        global trans_port  # pylint: disable = global-statement, invalid-name, global-variable-not-assigned
        global recv_data  # pylint: disable = global-statement, invalid-name, global-variable-not-assigned
        global recv_ircmd  # pylint: disable = global-statement, invalid-name, global-variable-not-assigned

        if DEBUG:
            _LOGGER.debug(
                "Send irTrans command cmd: %s res: %s offset: %i",
                cmd,
                res,
                offset,
            )
        msg = cmd + str(offset) + "\n"
        await IRTransCon.write_data(trans_port, msg)
        await asyncio.sleep(0.3)
        data = recv_data
        if len(data) > 0:
            if data[1] == res:  # pylint: disable=unsubscriptable-object
                mycfg["irtrans"] = "connected"
                return data[2].split(",")  # pylint: disable=unsubscriptable-object
            mycfg["irtrans"] = "Unknown answer from IRTrans: " + data
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
        global mycfg  # pylint: disable = global-statement, invalid-name, global-variable-not-assigned
        global trans_port  # pylint: disable = global-statement, invalid-name, global-variable-not-assigned
        global recv_data  # pylint: disable = global-statement, invalid-name, global-variable-not-assigned
        global recv_ircmd  # pylint: disable = global-statement, invalid-name, global-variable-not-assigned

        rsp = {"ircmd": "success"}
        msg = "Asnd " + remote + "," + command + "\n"
        if DEBUG:
            _LOGGER.debug("Command to send to IRTrans: %s", msg)
        await IRTransCon.write_data(trans_port, msg)
        await asyncio.sleep(0.3)
        data = recv_data
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
        global mycfg  # pylint: disable = global-statement, invalid-name, global-variable-not-assigned
        if DEBUG:
            _LOGGER.debug(
                "IRTRANS IR COMMAND(api_irtrans): %s : %s -> %s",
                mode,
                remote,
                command,
            )
        try:
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

                devices["hw_version"] = mycfg["version"][2] + " " + mycfg["version"][3]

                mycfg["devices"] = devices
            if mode == "SEND":
                mycfg = await cls.irtrans_snd_ir_command_async(cls, remote, command)
            return mycfg

        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error(
                "Something really wrong happened (api module)! - %s", exception
            )
