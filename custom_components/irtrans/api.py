"""Sample API Client."""
import logging
import asyncio
import socket

# from typing import Optional  # pylint: disable=unused-argument disable=unused-import

# import aiohttp
# from sockio.aio import TCP
import async_timeout

TIMEOUT = 10


_LOGGER: logging.Logger = logging.getLogger(__package__)

# HEADERS = {"Content-type": "application/json; charset=UTF-8"}


class IRTransApiClient:
    """API Client Class for IRTrans"""

    myresp = {"irtrans": "not connected", "devices": {}}

    def __init__(self) -> None:
        """IRTrans API Client"""
        # initialize TCP socket to IRTRans device
        try:
            with async_timeout.timeout(TIMEOUT):
                irsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                host, port = "192.168.2.226", 21000
                data = b"ASCI"  # Init, switch IRTRans API to ASCII mode
                irsocket.connect((host, port))
                irsocket.send(data)
                self._socket = irsocket
        except asyncio.TimeoutError as exception:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                "Time Out",
                exception,
            )

    def irtrans_snd_rcv(self, cmd: str, res: str, offset: int) -> list:
        """Send irTrans command and get result"""
        msg = bytes(cmd + str(offset) + "\n", "ascii")
        self._socket.send(msg)
        data = self._socket.recv(1024).decode("ascii")
        if len(data) > 0:
            data = data.split()
            if data[1] == res:
                self.myresp["irtrans"] = "connected"
            else:
                self.myresp["irtrans"] = "Unknown answer from IRTrans: " + data
                _LOGGER.debug(
                    "Unknown answer from IRTrans: %s",
                    data,
                )
        else:
            _LOGGER.error(
                "No answer from IRTrans",
            )
            raise Exception("No answer from IRTrans")
        return data[2].split(",")

    def irtrans_snd_ir_command(self, remote: str, command: str) -> dict:
        """Send IR command for specified remote to IRTrans"""
        rsp = {"ircmd": "success"}
        msg = bytes("Asnd " + remote + "," + command + "\n", "ascii")
        # _LOGGER.debug("Command to send to IRTrans: %s", msg)
        self._socket.send(msg)
        data = self._socket.recv(1024).decode("ascii")  #  **00018 RESULT OK
        if len(data) > 0:
            data = data.split()
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
            raise Exception("No answer from IRTrans")
        return rsp

    async def async_get_irtrans_data(self) -> dict:
        """Get data from IRTrans"""
        return await self.api_irtrans("GET", "", "")

    async def async_snd_irtrans_data(self, remote: str, command: str) -> dict:
        """Send data to IRTrans"""
        _LOGGER.debug(
            "IRTRANS IR COMMAND(async_snd_irtrans_data): %s -> %s",
            remote,
            command,
        )
        return await IRTransApiClient.api_irtrans(self, "SEND", remote, command)

    async def api_irtrans(self, mode: str, remote: str, command: str) -> dict:
        """IRTrans API handler"""
        try:
            async with async_timeout.timeout(TIMEOUT):
                if mode == "GET":
                    _LOGGER.debug(
                        "IRTRANS IR COMMAND(api_irtrans): %s : %s -> %s",
                        mode,
                        remote,
                        command,
                    )
                    # get first (max.) 3 REMOTES (offset = 0) from irTrans
                    devices = {}
                    remotes = []
                    remotes = self.irtrans_snd_rcv(
                        "Agetremotes ",
                        "REMOTELIST",
                        0,
                    )
                    last = int(remotes[1]) - 1
                    devices[remotes[3]] = []  # first Remote

                    i = 0
                    while i < last:  # get all Remotes from irTrans
                        i = i + 1
                        remotes = self.irtrans_snd_rcv(
                            "Agetremotes ",
                            "REMOTELIST",
                            i,
                        )
                        devices[remotes[3]] = []
                    # get all IR commands for every Remote (will be sensor attributes)
                    for device in devices:
                        offset = 0
                        resp = self.irtrans_snd_rcv(
                            "Agetcommands " + device + ",",
                            "COMMANDLIST",
                            offset,
                        )
                        commands = resp[3:]
                        offset = offset + int(resp[2])
                        while offset < int(resp[1]):
                            resp = self.irtrans_snd_rcv(
                                "Agetcommands " + device + ",",
                                "COMMANDLIST",
                                offset,
                            )
                            offset = offset + int(resp[2])
                            commands.extend(resp[3:])
                        devices[device] = commands

                    self.myresp["devices"] = devices
                    return self.myresp
                if mode == "SEND":
                    _LOGGER.debug(
                        "IRTRANS IR COMMAND(api_irtrans): %s : %s -> %s",
                        mode,
                        remote,
                        command,
                    )
                    return IRTransApiClient.irtrans_snd_ir_command(
                        self, remote, command
                    )
                return {}

        except asyncio.TimeoutError as exception:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                "Time Out",
                exception,
            )
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error("Something really wrong happened! - %s", exception)
