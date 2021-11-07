# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## [v0.11.0](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/tags/v0.11.0) - 2021-11-06

<small>[Compare with v0.10.0](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/compare/v0.10.0...v0.11.0)</small>
### Feature
* :sparkles: Add Custom Diff class to control order of operations. ([`0da4ff0`](https://github.com/networking/nautobot-plugin-device42-sync/commit/0da4ff07a8d039f1913a2c166bf29313ba729f32))
* :sparkles: Add method to find a site mapping from settings. ([`70f9a93`](https://github.com/networking/nautobot-plugin-device42-sync/commit/70f9a9369e705e3998073e18f9532a1738b6ff21))

### Fix
* :bug: Handle edge cases where device has A record for non-existent Subnet. ([`8fcfeb3`](https://github.com/networking/nautobot-plugin-device42-sync/commit/8fcfeb36082d3cae291240f5cbafa310c7b49cbc))

### Documentation
* :memo: Improve documentation in README and add information to RTD index ([`e9281ab`](https://github.com/networking/nautobot-plugin-device42-sync/commit/e9281abb6f21f374b82aef8d877427ecb89d4e3f))
* :memo: Improve typing and docstrings for some methods. ([`6058a95`](https://github.com/networking/nautobot-plugin-device42-sync/commit/6058a953a81128e9ebadf617d19dfa013cece5d5))

## [v0.10.0](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/tags/v0.10.0) - 2021-11-03

<small>[Compare with v0.9.3](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/compare/v0.9.3...v0.10.0)</small>

### Bug Fixes
- :bug: correct logging to be from diffsync. ([afb3b62](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/afb3b62c8896f665d97f37bb611ff73864794271) by Justin Drew - Network To Code).
- :bug: return sorted customfields. ([4f8066f](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/4f8066f57f520f9ccf597fbaecba49e7b3b8745e) by Justin Drew - Network To Code).
- :bug: missed exception var, has been added. ([d8ac88d](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/d8ac88d8355bd6adb8f231dca58faf608ccf62e4) by Justin Drew - Network To Code).
- :bug: check for dns answer matching primary ip needs str. ([87bf1cd](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/87bf1cdea2381731c8a8a22cd9f10ae76f7dac90) by Justin Drew - Network To Code).
- :bug: ensure customfields are sorted on both sides. ([d4be4a9](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/d4be4a9e96cc98fe00b885aed6ea24ea3909b982) by Justin Drew - Network To Code).
- :bug: remove `contact_info` attribute from provider. ([22887cf](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/22887cfbe6ad7fb0959fee092ad577d41df79937) by Justin Drew - Network To Code).
- :bug: validate it's dest port and device match, not source for z side. ([a40c0dd](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/a40c0dd3eb08446379188a738429e3f05bbd1c8f) by Justin Drew - Network To Code).
- :bug: corrected circuittermination to have circuit object passed. ([fe61e5a](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/fe61e5a316ef6c51c2ae0766cb831cd36dbfa7fd) by Justin Drew - Network To Code).
- :bug: correct exception to be nautobotvlan instead of site. ([9796647](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/9796647f74ea243248cd92d261040a94cc4f34ac) by Justin Drew - Network To Code).
- :bug: change `cid` finally. ([5049d8c](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/5049d8cf35a1f892a61e0531f09bd096c6cc1143) by Justin Drew - Network To Code).

### Features
- :sparkles: add methods to get default customfields for ports and subnets. ([6acf222](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/6acf2225eecdabb9112fbb213fb41dec7f7be59e) by Justin Drew - Network To Code).
- :sparkles: handle case for ip addr where device changes. ([7d0ba67](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/7d0ba672964f14ce690534683c75fd5bd860a236) by Justin Drew - Network To Code).


## [v0.9.3](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/tags/v0.9.3) - 2021-11-01

<small>[Compare with v0.9.2](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/compare/v0.9.2...v0.9.3)</small>

### Bug Fixes
- :rewind: revert attribute for circuit object to use cid. ([d856e3e](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/d856e3eeb084f65b4fcd83774ffeab20c510b5b8) by Justin Drew - Network To Code).


## [v0.9.2](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/tags/v0.9.2) - 2021-11-01

<small>[Compare with v0.9.1](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/compare/v0.9.1...v0.9.2)</small>

### Bug Fixes
- :bug: correct attribute from `cid` to `circuit_id` for circuitterminations ([134943d](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/134943d00116c1bb9f66cb6a40d846a8c71e656f) by Justin Drew - Network To Code).


## [v0.9.1](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/tags/v0.9.1) - 2021-11-01

<small>[Compare with v0.6.0](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/compare/v0.6.0...v0.9.1)</small>

### Features
- Add circuit terminations to devices in create ([ed908b0](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/ed908b0321e71969ca076f83b15a49fcb39bbcc7) by Justin Drew - Network To Code).
- Add telco circuits ([e1c0386](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/e1c03862aeb2e584bfd49996b5349ff4561574fa) by Justin Drew - Network To Code).
- Add custom fields ([e52bb0d](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/e52bb0d2faa4170e207a288c3e7b6e74e3ae7818) by Justin Drew - Network To Code).
- Add cables ([f1c9791](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/f1c9791b9b8b1e63f52e04d002e62732be27af20) by Justin Drew - Network To Code).
- Add vlans and trunks ([8b58eb4](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/8b58eb4f8cb33c7887ee4822f63656da4db51e66) by Justin Drew - Network To Code).
- Add facility ([df64403](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/df644032d836fb9a935713e0f60cab19d1730d3f) by Justin Drew - Network To Code).
- Add device roles ([5f4a488](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/5f4a4880c38e48cb9c5d8550ba0096f06b1d2510) by Justin Drew - Network To Code).
- Add tags ([929ef2b](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/929ef2b75195b8db11894cd69bc4b2a450cebd69) by Justin Drew - Network To Code).

### Bug Fixes
- :bug: fix customfields not being added to ipaddress ([36a1dad](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/36a1dadfedd6d0f3a45364757cd0e00b7ad8118c) by Justin Drew - Network To Code).
- Fix tests ([d224c76](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/d224c768bdcb3802b9243ea0236e6e1ad10dde1c) by Justin Drew - Network To Code).
- Fix diffs ([5b5e8fe](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/5b5e8fe5a4a400771be8dc5c6c1bc039481daeb1) by Justin Drew - Network To Code).
- Fix model updates ([51bae7e](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/51bae7e43aff2af6557315987b03e0132ccad0b2) by Justin Drew - Network To Code).
- Fix platform ([81da171](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/81da171a683c7f211b4d0d0200ee778bfa10ca84) by Justin Drew - Network To Code).
- Fix ip assignment ([53c8e70](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/53c8e70a197067ca62dd1e9abc62ec8c4cb02946) by Justin Drew - Network To Code).
- Fix vrf to use obj, not name ([9877ff2](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/9877ff25af995722490f56749f822f4b2b612d53) by Justin Drew).


## [v0.6.0](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/tags/v0.6.0) - 2021-08-27

<small>[Compare with v0.4.1](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/compare/v0.4.1...v0.6.0)</small>

### Added
- Add ip addresses ([afdcaae](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/afdcaae2b202978fc71ab082d1933cf79c27868c) by Justin Drew - Network To Code).
- Add prefixes ([9fe3086](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/9fe3086e959e1b198c572f6a5b8856ee73d50dac) by Justin Drew - Network To Code).
- Add vrfs ([8ccaf12](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/8ccaf128a62d2125c4fa34b5ab425af2b2aaf925) by Justin Drew - Network To Code).
- Add ports ([9873430](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/9873430a23bac50cf3d6b1451163e43602051b67) by Justin Drew - Network To Code).


## [v0.4.1](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/tags/v0.4.1) - 2021-08-17

<small>[Compare with v0.3.0](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/compare/v0.3.0...v0.4.1)</small>

### Added
- Add clusters and devices ([116b741](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/116b741747e7f0d4f77b5ab78f703e5e934a8f5e) by Justin Drew - Network To Code).
- Add vendors ([860f9fc](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/860f9fc5bc8df502bc1d61db300bb9f1a0ca241e) by Justin Drew).
- Add racks ([13e92fa](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/13e92fa1f6a644c2728a9eaa6382e40d263c73e9) by Justin Drew - Network To Code).


## [v0.3.0](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/tags/v0.3.0) - 2021-07-28

<small>[Compare with v0.2.0](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/compare/v0.2.0...v0.3.0)</small>

### Added
- Add site sync support ([4c6ac8f](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/4c6ac8f2e516f9311daa1e7441b834e53793644d) by Justin Drew - Network To Code).


## [v0.2.0](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/tags/v0.2.0) - 2021-07-15

<small>[Compare with v0.1.0](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/compare/v0.1.0...v0.2.0)</small>


## [v0.1.0](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/tags/v0.1.0) - 2021-07-15

<small>[Compare with first commit](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/compare/41ddaf01ba6afd1d8f91be6264e634f6c37428fb...v0.1.0)</small>
