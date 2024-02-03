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

## Installation
### Install with HACS (recommended)

[HACS](https://community.home-assistant.io/t/custom-component-hacs) can be used to install this integration. Just search for iRTrans and install it directly from HACS. HACS will keep track of updates and you can easily upgrade iRTrans to latest version.
If iRTrans is not (yet) available when using the `Explore & Download Repositories` in the HACS page use the menu (three dots) in the upper right corner to add a `Custom Repository` : https://github.com/schwarzenbergf/irtrans.git .

![Add Custom Repository](/custom_components/irtrans/images/add2hacs.png)

After adding this [repository](https://github.com/schwarzenbergf/irtrans.git) and adding iRTrans to HACS (`Explore & Download Repositories`) do not forget to restart HA.

### Install manually

1. Install this integration by creating a `custom_components` folder in the same folder as your configuration.yaml, if it doesn't already exist.
2. Create another folder `irtrans` in the `custom_components` folder. Copy all files from [irtrans](/custom_components/irtrans) into the `irtrans` folder. Do not copy files from master branch, download latest release (.zip) from [here](https://github.com/schwarzenbergf/irtrans/releases) and copy the content of `custom_components/irtrans/` to the a/m irtrans folder.

### Configuration is done in the UI

After installing iRTrans (and the required restart of HA), add iRTrans to HA via

`Settings` --> `Devices & Services`.

Just use `Add Integration` button and search for iRTrans. Fill in `Host Address` & `Port` (default 21000) of the iRTrans device and you are done.

![Config](/custom_components/irtrans/images/config_ui.png)

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
