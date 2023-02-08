[![hacs][hacsbadge]][hacs]
[![Community Forum][forum-shield]][forum]
[![License][license-shield]](LICENSE)
![GitHub release (beta)][beta-shield]
![Project Maintenance][maintenance-shield]

![irtrans](/custom_components/irtrans/images/logo.png)

# iRTrans - this is a BETA release
_Component to integrate with [irtrans](http://www.irtrans.de/en/shop/lan.php)._

**This component will set up the following platforms.**

Platform | Description
-- | --
`irtrans` | Sensor - Show content from iRTrans LAN device
`event`  | Event Triggers from (learned) Remotes
`service` | Service call for each Remote to send IR commands

***

## Requirements
iRTrans appliances are devices which are able to send and receive (and to learn) IR (infrared) signals.
For more details see [here](http://www.irtrans.de/en/shop/lan.php).
This integration supports only so called `LAN` devices (which have an Ethernet or WiFi connection).
It has been tested with a device with IR Database and works probaly just with such a device.
Learning of IR signals is not (yet) supported. There are good [applications](http://www.irtrans.de/en/download/) from iRTrans GmbH to do this.

## How it works
The communication with the iRTrans device follows [these API rules](https://www.irtrans.de/download/Docs/iRTrans%20TCP%20ASCII%20Interface_EN.pdf).

The basic procedure works as follows:

After successfully connected to an iRTrans device the configuration is read from the device. In the first step all the IR Remotes are fetched. In the second step for each Remote all available commands are read. Remotes and associated commands (buttons) are then stored as attributes of the Sensor entity, which will be created as representation of the iRTrans device.

![irtrans_sensor](/custom_components/irtrans/images/irtrans_sensor.png)

**Sending IR commands**

For each Remote a so called `entity_service` will be created with the following naming convention:

send_irtrans_ir_command_*remote_name*

where *remote_name* is the name of a (learned) IR Remote.
This service can be used to fire IR commands. Here is an example how it looks in `Developer Tools`:

![Developer Tools](/custom_components/irtrans/images/devtools_example.png)

`Automations` can also be used to fire IR commands. Here is an example for an `Automation Action`:

```yaml
description: "Fire IR command for vol+ of Remote lgsmarttv"
mode: single
trigger: []
condition: []
action:
  - service: irtrans.send_irtrans_ir_command_lgsmarttv
    data:
      remote: lgsmarttv
      ir_cmd: vol+
    target:
      entity_id: sensor.irtrans_sensor
```

**Listening to IR commands**

The integration provides event support for IR commands which has been received by the iRTrans device.
Only IR commands which are known (learned) by the iRTrans device will trigger an event.
Here is an example for an `Automation Trigger` on an iRTrans event:

```yaml
description: "Trigger on button vol+ from Remote lgsmarttv"
mode: single
trigger:
  - platform: event
    event_type: irtrans_event
    event_data:
      remote: lgsmarttv
      button: vol+
condition: []
action: []
```

## Installation
### Install with HACS (recommended)

[HACS](https://community.home-assistant.io/t/custom-component-hacs) can be used to install this integration. Just search for iRTrans and install it directly from HACS. HACS will keep track of updates and you can easily upgrade iRTrans to latest version.

### Install manually

1. Install this integration by creating a `custom_components` folder in the same folder as your configuration.yaml, if it doesn't already exist.
2. Create another folder `irtrans` in the `custom_components` folder. Copy all files from [irtrans](/custom_components/irtrans) into the `irtrans` folder. Do not copy files from master branch, download latest release (.zip) from [here](https://github.com/schwarzenbergf/irtrans/releases) and copy the content of `custom_components/irtrans/` to the a/m irtrans folder.

### Configuration is done in the UI

After installing iRTrans (and the required restart of HA), add iRTrans to HA via

`Settings` --> `Devices & Services`.

Just use `Add Integration` button and search for iRTrans. Fill in `Host Address` & `Port` (default 21000) of the iRTrans device and you are done.

![Config](/custom_components/irtrans/images/config_ui.png)

<!---->


### Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***
[license-shield]: https://img.shields.io/github/license/schwarzenbergf/irtrans?style=for-the-badge
[beta-shield]: https://img.shields.io/github/v/release/schwarzenbergf/irtrans?include_prereleases&style=for-the-badge
[irtrans]: https://github.com/custom-components/irtrans
[commits]: https://github.com/custom-components/irtrans/commits/master
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[irtransimg]: ![irtrans](/custom_components/irtrans/irtrans/logo.png)
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40schwarzenbergf-blue.svg?style=for-the-badge
[user-profile]: https://github.com/schwarzenbergf

