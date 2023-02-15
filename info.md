[![hacs][hacsbadge]][hacs]
[![Community Forum][forum-shield]][forum]
[![License][license-shield]](LICENSE)
![Github release latest](https://img.shields.io/github/v/release/schwarzenbergf/irtrans?style=for-the-badge)
![Project Maintenance][maintenance-shield]
![irtrans](/custom_components/irtrans/images/logo.png)

# iRTrans
_Component to integrate with [irtrans](http://www.irtrans.de/en/shop/lan.php)._

**This component will set up the following platforms.**

Platform | Description
-- | --
`irtrans` | Sensor - Show content from iRTrans LAN device
`event`  | Event Triggers from (learned) Remotes
`service` | Service call for each Remote to send IR commands

iRTrans appliances are devices which are able to send and receive (and to learn) IR (infrared) signals.
For more details see [here](http://www.irtrans.de/en/shop/lan.php).
This integration supports only so called `LAN` devices (which have an Ethernet or WiFi connection).
It has been tested with a device with IR Database and works probaly just with such a device.
Learning of IR signals is not (yet) supported.
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
