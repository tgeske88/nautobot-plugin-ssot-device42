# Nautobot SSoT Device42

TODO: Write plugin documentation, the outline here is provided as a guide and should be expanded upon.  If more detail is required you are encouraged to expand on the table of contents (TOC) in `mkdocs.yml` to add additional pages.

## Description

This plugin was written to handle synchronization of data from Device42 into Nautobot.

## Installation

There are two ways of installing this plugin, either via PyPI or pulling directly from Git.

## Configuration

In order to use this plugin you must have the Device42 settings configured at a bare minimum:

__*device42_host*__ - The fully-qualified domain name for your Device42 instance. Must include the URL schema, ie http or https. This value is currently set via the `DEVICE42_HOST` environment variable. It's advised to continue with this method for best security. Value is expected to be a string.

__*device42_username*__ - The username of the account you wish to use to synchronize with Device42. This account requires read-only permissions. It's advised to use a service account for best security. This value is currently set via the `DEVICE42_USERNAME` environment variable. It's advised to continue with this method for best security. Value is expected to be a string.

__*device42_password*__ - The password of the account used with the `device42_username` setting. This value is currently set via the `DEVICE42_PASSWORD` environment variable. It's advised to continue with this method for best security. Value is expected to be a string.

__*verify_ssl*__ - This setting will determine whether the plugin will validate the SSL certificate of your Device42 instance when connecting. This is useful for test instances where you might be using a self-signed certificate and want to ignore the invalid certificate errors. Value is expected to be a boolean.

In addition, there are some default values configured in the plugin settings that are required:

__*defaults["site_status"]*__ - This setting defines the default Status for a Site. This is in case Device42 is missing this information. Value is expected to be a string.

__*defaults["rack_status"]*__ - This setting defines the default Status for a Rack. This is in case Device42 is missing this information. Value is expected to be a string.

__*defaults["device_role"]*__ - This setting defines the default Role for a Device. This is in case Device42 is missing this information. Value is expected to be a string.

Finally, there are some optional settings that enable the plugin to handle the Device42 import data in a more specific way:

__*use_dns*__ - This option will have the plugin perform a DNS query of the Device's hostname to see if there is an A record. If there is, it will assign that as the Device's primary IP address. If it is unable to determine the interface to assign that IP address to, it will create a Management interface on the Device. Value is expected to be a boolean.

__*customer_is_facility*__ - This option is for the use case where the Device42 Customer field is used to denote a Site's facility instead of a Customer (department, division, tenant). Value is expected to be a string.

__*facility_prepend*__ - This option tells the plugin which string is prepended in a Tag to determine a Device's facility. This is used in conjunction with the `customer_is_facility` option. Value is expected to be a string.

__*role_prepend*__ - This option tells the plugin which string is prepended in a Tag to determine a Device's Role. This is due to Device42 not having a specific device role field. Value is expected to be a string.

__*verbose_debug*__ - This option will enable more verbose debug logging to be produced. This option should be use cautiously as it can produce a large amount of returned data. Value is expected to be a boolean.

__*hostname_mapping*__ - This option enables the ability for a Device to be assigned to a Site based upon its hostname. The value is expected to be a list of dictionaries with the key being the regex used to match the hostname and the value is the slug of the Site to assign to the Device. This option takes precedence over the `customer_is_facility` determination of a Device's Site with the Building denoted in Device42 being the last resort.

## Usage

This plugin has been validated to work with Nautobot v1.1.0-1.1.4 and has been validated against Device42 v17.02.00.1622225288. It currently supports importing data from Device42 into Nautobot but not the reverse.

## API

*TBD*

## Views

This plugin does not add any custom views to Nautobot at this time. It extends the [SSoT plugin](https://github.com/nautobot/nautobot-plugin-ssot) and uses the views from that plugin.

## Models

This plugin currently supports importing the following models from Device42:

- Buildings
- Rooms
- Racks
- Vendors
- Hardware
- Devices
- Ports
- Connections
- VRF Groups
- Subnets
- IP Addresses
- VLANs
- Telco Circuits

Due to requirements for model creation in Nautobot, the following requirements on the data in Device42 must be followed for data to be imported into Nautobot:

### Buildings

- Buildings must have a tag with what is defined by `sitecode_prepend` setting in order to fill in facility (site code)

### Rooms

- must have a Building specified
- name must be unique

### Racks

- must have Building and Room specified.
- name must be unique

### Hardware Models

- must have a Manufacturer specified

### Devices

- must have at least Building or Customer specified
- must have the Hardware model specified

  __NOTE__: Device Platform has a different use for each section as follows:

  - platform name: ansible_network_os name
  - platform slug: netmiko name
  - napalm_driver: napalm driver name
    This allows you to use the inventory from Nautobot for most network automation tasks without needing to map the platform.

### Vendors

- Vendor connected to a Hardware Model must match the Vendor for the Platform (OS), ie Aironet devices running IOS must be under same name as Catalyst, etc.

### Ports

- must have a name 
- must have a switch or device assigned to it
- interface speed will attempt to be determined based upon the discovered speed from Device42 and failing that, the interface name.

### VLANs

- If duplicate VLANs are found when attaching to an Interface for trunking, the first found will be used.
- VLAN 0 is invalid VID in Nautobot and will not be imported.
- If unable to determine site for a VLAN, it will attempt to search for a VLAN with matching name and VLAN ID that doesn't have a Site attached. This is caused by Devices that don't have a Building or Customer specified in Device42.
