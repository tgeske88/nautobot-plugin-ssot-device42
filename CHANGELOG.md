# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## v0.15.0 (2022-01-13)
### Feature
* :sparkles: Add method for get_hardware_models along with tests for importing into adapter and loading data from D42 ([`03df0fa`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/03df0fad5fa692255fa458905fb549ad68c76961))
* :sparkles: Add plugin setting to prevent deletion of objects during sync. ([`12256eb`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/12256eb1929a0c4e8893d96299850c871ecfe355))
* :sparkles: Add method get_vendors along with tests to validate functionality ([`23de09d`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/23de09d1eb9556aac973079dd5b5142725bca9ae))
* :sparkles: Add support for importing Patch Panels from Assets along with the Front/Rear ports. ([`b831cea`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/b831cea1f266c044deccbbf65125cb3196441913))
* :sparkles: Add method to get Racks mapped to their primary key and test validating it ([`b3552fe`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/b3552fe55ee7f7f59d531876eaa5ca8e61ac18aa))
* :sparkles: Add method to make mapping of Customer to their primary key ([`3cbc90e`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/3cbc90e2568c437634c6d5093d61d03b414e1344))
* :sparkles: Add method to get Rooms mapped to their primary keys for reference ([`bdad3cb`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/bdad3cb07cc23994960c8e3286a2df45a943e841))
* :sparkles: Add a method and tests to get Buildings mapped to their primary key ([`427580a`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/427580a5b9ef7ceefea14e4171d6bef1e0a761e6))
* :sparkles: Add method to obtain patch panels and create dict with PK as key ([`e8d5440`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/e8d544071998addbbcc39df4227188c8f158b943))

### Fix
* :bug: Handle duplicate IP Addresses being imported from Device42 ([`7e00d6f`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/7e00d6f49a3e5b2531e0bb5bf989cd0658b8661a))
* :bug: Add handling for ValidationErrors in case they occur ([`332de8b`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/332de8b4bc2a5c0fbd1fb0bb31e76dab28e02994))
* :bug: Fix issue where multiple devices are assigned to same U position in a Rack. ([`c70d8c3`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/c70d8c3e2b3ee7b77c18b6ef839ff91fdec53610))
* :bug: Fix the get_patch_panels DOQL query ([`27319d6`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/27319d6290a0b2f12ad4abce422fced094a7580c))
* :bug: Fix check for debug logging ([`982dc12`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/982dc12f4db8d773ab185222f3e2ca20519f05fc))
* :rotating_light: Add null attributes to object creations to address pydantic warning ([`dd37942`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/dd379428209f6061e5a1c1140ffa8ea784d02f93))
* :bug: Prevent duplicate ports from being loaded. ([`1e56f23`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/1e56f23e1508a695efbb4102a392543e7a9712a6))
* :bug: Use UUID to find VRF to delete ([`188d7e5`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/188d7e518d9d6cb86be87ac9ec6355361308caf7))
* :bug: Remove get_circuit_status call when setting Circuit status in update ([`46e1c2c`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/46e1c2c3a128b240c36863c4842544041e5e6a33))
* :bug: Make objects_to_delete a public variable and make it a defaultdict ([`024bc1b`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/024bc1bce3a8fd7c0e0f24d887172a4361597a68))
* :bug: Remove object from logging statements ([`db4b1b4`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/db4b1b4ec470813be9b7e06754fd20366b3213a7))
* :bug: Fix verbose debug logging ([`e7c541c`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/e7c541c5c6e437b698b8059db6511961913be66a))
* :bug: Add rack position for patch panel model and update test to include it ([`4878d5c`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/4878d5ced79626f86c5e91c8e9caf274bfb62cfd))

### Documentation
* :memo: Fix link for 0.13.1 documentation in CHANGELOG ([`8ab1f96`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/8ab1f96789690effeeeb0ddcef8a7c8816cd1864))
* :memo: Add documentation on requirements for Subnets and Telco Circuit imports ([`67b6b30`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/67b6b304a5a5c32fbfb426ce969f6d3e80d61edc))
* :memo: Remove mention of verbose_debug setting in docs ([`a03dcb3`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/a03dcb332fcaf45a08e2991a9e81030c373357a1))
* :memo: Correct docstring for circuit models ([`aac72ac`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/aac72aca88f8225e1bfebad6f853e05682ca9da2))

## [v0.14.0](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/tags/v0.13.1) -  (2021-12-20)
### Feature
* :zap: Add UUID attribute to all models for the Nautobot Data Target. ([`07c8a40`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/07c8a408efc1615536077f66680cd5a5b0dec267))

### Fix
* :bug: Tweak device import to ignore those where a Building can't be found. ([`a59fd82`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/a59fd82d18ed25a678455492e7134a9d8eac9cc4))
* :bug: Include VRF when trying to find IP Address for update ([`a164592`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/a164592a8dd959e5dc54027a887d84c026482338))
* :bug: Fix infinite loop ([`6c5d2e5`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/6c5d2e525b6d8a19ab38d1c9f8ba40739303d917))
* :bug: Tweak find_ipaddr and set_primary_from_dns methods to have IP Address returned once found. ([`b3f62db`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/b3f62db91262236fb4df18a656f103c52cfaa43a))
* :bug: Fix infinite loop when looking for IP in VRF ([`4d792eb`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/4d792eb573dfc65bbc3bad9054e3c0d675792cfe))
* :bug: Update IP Address delete to handle multiple results ([`e8478be`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/e8478bec62155ddc24b74c5e831df0a5a15d181d))
* :bug: Rewrite find_ipaddr to check VRFs ([`a6592b8`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/a6592b8613b6fce58090692364cd1720592d41b1))
* :bug: Subnet/IPAddress delete methods updated to look for vrf__name ([`d53badf`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/d53badf904cd4f4cf82d8e3f0fcc971507fed314))
* :bug: Add VRF as identifier to IP Address ([`20a1fa0`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/20a1fa0a0e247882688445c88afd12991e5fe3d5))
* :bug: Ensure all logging sends to message. ([`874db65`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/874db650278d278f0b84fa933169dec40cc25658))

## [v0.13.1](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/tags/v0.13.1) -  (2021-12-15)

<small>[Compare with v0.13.0](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/compare/v0.13.0...v0.13.1)</small>

### Testing

* Added unittests for Device42 util methods.

## [v0.13.0](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/tags/v0.13.0) - 2021-12-09

<small>[Compare with v0.12.0](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/compare/v0.12.0...v0.13.0)</small>

### Feature
* :sparkles: Add support for Device Lifecycle Management plugin for software version tracking. ([`e578f0e`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/e578f0e9886ffd451dc9bbe7455a1dd1664e43f5))
* :heavy_plus_sign: Start adding support for Device Lifecycle plugin ([`e6806df`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/e6806df829cc3fbfeb33f2b389161cf619703f5a))

### Fix
* :bug: Change Port deletion to standard method instead of delayed. ([`056c117`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/056c1178135d117e7b9dcf7bda0fe17c68b13e81))
* :bug: Update find_ipaddr method to allow for IPv6 and all subnets in IPv4. ([`3e10fb0`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/3e10fb0c0ae26597820bb59e31299d7f8c9c7437))
* :bug: Add provider to _objects_to_delete dict ([`09a3aad`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/09a3aaddb24a2759f8110bd3fce8be20abbd3008))
* :bug: Update Circuit processing to handle Circuits/Connections without terminations. ([`000d0e7`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/000d0e7bb80d07652cda6b1b958fc73c59069006))
* :bug: Validate VLAN PK is in vlan_map ([`c31cede`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/c31cede201435c7b2bb40ee02ed4d0ca81231303))
* :bug: Ensure that the object is always returned for accurate logs. ([`d16dbba`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/d16dbbaeb10618c3fcdae3278ca3fb2aae59bca8))
* :bug: Validate Circuit has termination when loading ([`8f6d7d3`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/8f6d7d34c38b75b4e0fd873baaf3a91e1f6a76f8))
* :bug: Ensure that logs are sent in message. ([`6de3553`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/6de355338a5c5d5cbe55082b83d6ca4dd054d95e))
* :bug: Fix APs being processed as FQDNs. ([`469123e`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/469123ec4dc046b34829d86d2fb958837fece7bd))
* :bug: Provider account number is limited to 30 characters. ([`4183a65`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/4183a65f89bd93f8f1a09129c0ba2d79b9ac01ce))
* :bug: Fix the a/z side connections to Device Ports ([`545ec66`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/545ec6680b046000a7df79bf538435d2c9f6699d))
* :bug: Ensure that the first spot is reserved for master device in VC ([`b5d7884`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/b5d7884eab6b79deea6186724b9a0c7ea5ab8ceb))

### Documentation
* :memo: Correct name of project in docstring ([`8090ecb`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/8090ecb0f51f99daf554af5808636468430930ae))

### Performance
* :white_check_mark: Add test for get_vlans_with_location method ([`6e5714a`](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/commit/6e5714a269bb625a1f3f4fbd36a9022128b2f1f4))

## [v0.12.0](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/tags/v0.12.0) - 2021-11-09

<small>[Compare with v0.11.0](https://gitlab.corp.zmi.global/networking/nautobot-plugin-device42-sync/compare/v0.11.0...v0.12.0)</small>

### Feature
* :sparkles: Add `ignore_tag` feature to allow Devices to not be imported based on a Tag. ([`0bbca1f`](https://github.com/networking/nautobot-plugin-device42-sync/commit/0bbca1f4e179a6b5fc8e494a690a992e1118ed1d))

### Fix
* :bug: Fix catch for AP hosts. ([`495238e`](https://github.com/networking/nautobot-plugin-device42-sync/commit/495238e48897ed8402c00f73fc5578efbb9ae408))
* :bug: Should have used continue instead of break. ([`2d8a6b0`](https://github.com/networking/nautobot-plugin-device42-sync/commit/2d8a6b06bcc847f2cc13b66a61455b91f9a8b4bb))
* :bug: Handle case where IP is assigned as primary to another device. ([`dfd113f`](https://github.com/networking/nautobot-plugin-device42-sync/commit/dfd113f7b9473a4d03c95829effc887debd7f8aa))
* :bug: Correct job logging to come from diffsync object in models. ([`92871c0`](https://github.com/networking/nautobot-plugin-device42-sync/commit/92871c03c1b8533d7e9efed441340619ec35102a))

### Documentation
* :memo: Add documentation for `ignore_tag` feature. ([`3ab83d6`](https://github.com/networking/nautobot-plugin-device42-sync/commit/3ab83d688a6d4bf236ba0aeb1cc403d4d318b99a))

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
