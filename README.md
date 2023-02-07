[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
[![Community Forum][forum-shield]][forum]

# irtrans - In development / not ready yet

_Component to integrate with [irtrans](http://www.irtrans.de/de/shop/lan.php)._

## Intro
This integration adds support for [IRTrans Ethernet devices](http://www.irtrans.de/de/shop/lan.php) to Home Assistant. For now it has been testet with (and supports) only *IRTrans LAN DB (with database) devices*. The communication with the IRTrans device follows [these API rules](https://www.irtrans.de/download/Docs/IRTrans%20TCP%20ASCII%20Interface_EN.pdf).

The basic procedure works as follows:

After successfully connected to a IRTrans device the configuration is read. In the first step all the (learned) IR Remotes are fetched. In the second step for each Remote all available commands are read. Remotes and associated commands (buttons) are then stored as attributes of the Sensor entity, which will be created as representation of the IRTrans device.

![irtrans_sensor](/custom_components/irtrans/images/irtrans_sensor.png)

**Sendig IR commands**

For each Remote a so called `entity service` will be created with the following naming convention:

send_irtrans_ir_command_*remote_name*

where *remote_name* is the name of a (learned) IR Remote.

This service can be used to fire IR commands. Here is an example how it looks in `Developer Tools`:

![Developer Tools](/custom_components/irtrans/images/devtools_example.png)

`Automations` can be also used to fire IR commands. Here is an example for an `Automation Action`:

```yaml
        description: "Fire IR command for `vol+`of Remote *lgsmarttv*"
        mode: single
        trigger: []
        condition: []
        action:
          - service: irtrans.send_irtrans_ir_command_*lgsmarttv*
            data:
              remote: *lgsmarttv*
              ir_cmd: *vol+*
            target:
              entity_id: sensor.irtrans_sensor
```

**This component will set up the following platforms.**

Platform | Description
-- | --
`irtrans` | Sensor - Show content from IRTrans LAN device
`event`  | Event Triggers from (learned) Remotes
`service` | Service call for each Remote

![irtrans](/custom_components/irtrans/images/logo.png)

## Installation

## Configuration is done in the UI

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***
[license-shield]: https://img.shields.io/github/license/schwarzenbergf/irtrans
[irtrans]: https://github.com/custom-components/irtrans
[commits]: https://github.com/custom-components/irtrans/commits/master
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[irtransimg]: ![irtrans](/custom_components/irtrans/irtrans/logo.png)
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[maintenance-shield]: https://img.shields.io/maintenance/yes/2023
[releases]: https://github.com/custom-components/irtrans/releases
