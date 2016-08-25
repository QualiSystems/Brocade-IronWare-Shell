#!/usr/bin/python
# -*- coding: utf-8 -*-

import inject
import os
import re

from cloudshell.configuration.cloudshell_snmp_binding_keys import SNMP_HANDLER
from cloudshell.configuration.cloudshell_shell_core_binding_keys import LOGGER

from cloudshell.networking.autoload.networking_attributes import RootAttributes, ChassisAttributes, PowerPortAttributes, \
    ModuleAttributes, SubModuleAttributes, PortAttributes, PortChannelAttributes
from cloudshell.networking.autoload.networking_model import RootElement, Chassis, Module, SubModule, Port, PowerPort, \
    PortChannel
from cloudshell.networking.brocade.utils import sort_elements_by_attributes
from cloudshell.networking.operations.interfaces.autoload_operations_interface import AutoloadOperationsInterface
from cloudshell.shell.core.config_utils import override_attributes_from_config


class NetIronSnmpAutoload(AutoloadOperationsInterface):
    FILTER_PORTS_BY_DESCRIPTION = ['bme', 'vme', 'me', 'vlan', 'gr', 'vt', 'mt', 'mams', 'irb', 'lsi', 'tap']
    FILTER_PORTS_BY_TYPE = ['tunnel', 'other', 'pppMultilinkBundle', 'mplsTunnel', 'softwareLoopback']
    SUPPORTED_OS = [r'IronWare']

    def __init__(self, snmp_handler=None, logger=None):
        self._logical_generic_ports = {}
        self._physical_generic_ports = {}
        self._generic_physical_ports_by_description = None
        self._generic_logical_ports_by_description = None
        self._ports = {}
        self.sub_modules = {}
        self._modules = {}
        self._chassis = {}
        self._root = RootElement()

        self._snmp_handler = None
        self.snmp_handler = snmp_handler

        self._ipv4_table = None
        self._ipv6_table = None
        self._if_duplex_table = None
        self._autoneg = None

        self._logger = logger
        """Override attributes from global config"""
        overridden_config = override_attributes_from_config(BrocadeSnmpAutoload)
        self._supported_os = overridden_config.SUPPORTED_OS

    @property
    def logger(self):
        if self._logger is not None:
            return self._logger
        return inject.instance(LOGGER)

    @property
    def snmp_handler(self):
        if self._snmp_handler is None:
            self.snmp_handler = inject.instance(SNMP_HANDLER)
        return self._snmp_handler

    @snmp_handler.setter
    def snmp_handler(self, snmp_handler):
        if snmp_handler:
            snmp_handler.snmp_request = self.snmp_request
            self._snmp_handler = snmp_handler
            self._initialize_snmp_handler()

    @property
    def ipv4_table(self):
        if not self._ipv4_table:
            self._ipv4_table = sort_elements_by_attributes(
                self._snmp_handler.snmp_request(('IP-MIB', 'ipAddrTable')), 'ipAdEntIfIndex')
        return self._ipv4_table

    @property
    def ipv6_table(self):
        if not self._ipv6_table:
            self._ipv6_table = sort_elements_by_attributes(
                self._snmp_handler.snmp_request(('IPV6-MIB', 'ipv6AddrEntry')), 'ipAdEntIfIndex')
        return self._ipv6_table

    @property
    def generic_physical_ports_by_description(self):
        if not self._generic_physical_ports_by_description:
            self._generic_physical_ports_by_description = {}
            for index, generic_port in self._physical_generic_ports.iteritems():
                self._generic_physical_ports_by_description[generic_port.port_description] = generic_port
        return self._generic_physical_ports_by_description

    @property
    def generic_logical_ports_by_description(self):
        if not self._generic_logical_ports_by_description:
            self._generic_logical_ports_by_description = {}
            for index, generic_port in self._logical_generic_ports.iteritems():
                self._generic_logical_ports_by_description[generic_port.port_description] = generic_port
        return self._generic_logical_ports_by_description

    def snmp_request(self, request_data):
        if len(request_data) == 2:
            result = self.snmp_handler.walk(request_data)
        elif len(request_data) > 2:
            result = self.snmp_handler.get_property(*request_data)
        else:
            raise Exception('_snmp_request', 'Request tuple len has to be 2 or more')
        return result

    def _initialize_snmp_handler(self):
        # path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mibs'))
        # self.snmp_handler.update_mib_sources(path)
        self.logger.info("Loading mibs")
        self.snmp_handler.load_mib('IF-MIB')
        self.snmp_handler.load_mib('ENTITY-MIB')
        self.snmp_handler.load_mib('IEEE8023-LAG-MIB')
        self.snmp_handler.load_mib('EtherLike-MIB')
        self.snmp_handler.load_mib('IP-MIB')
        self.snmp_handler.load_mib('IPV6-MIB')

    def _get_element_id(self, element_id, entity_table=None):
        """ Get element_id according to the device structure and networking standard

        :return Return parent id if parent element in container or backplane
        """
        entity_table = entity_table or self.snmp_handler.snmp_request(('ENTITY-MIB', 'entPhysicalTable'))
        parent_id = int(entity_table[element_id]['entPhysicalContainedIn'])
        if parent_id > 0 and parent_id in entity_table:
            if re.search(r'container|backplane', entity_table[parent_id]['entPhysicalClass']):
                return parent_id
        return element_id

    def _is_sub_module(self, element_id, entity_table=None):
        """ Check if current element is sub module

        :return True or False
        """
        entity_table = entity_table or self.snmp_handler.snmp_request(('ENTITY-MIB', 'entPhysicalTable'))
        parent_id = int(entity_table[element_id]['entPhysicalContainedIn'])
        if parent_id > 0 and parent_id in entity_table and entity_table[parent_id]['entPhysicalClass'].replace("'", "") == "module":
                return True
        return False

    def _is_valid_device_os(self):
        """ Validate device OS using snmp

            :return: True or False
        """

        system_description = self.snmp_handler.snmp_request(('SNMPv2-MIB', 'sysDescr', 0))
        self.logger.debug('Detected system description: \'{0}\''.format(system_description))
        result = re.search(r"({0})".format("|".join(self._supported_os)),
                           system_description,
                           flags=re.DOTALL | re.IGNORECASE)

        if result:
            return True
        else:
            error_message = 'Incompatible driver! Please use this driver for \'{0}\' operation system(s)'. \
                format(str(tuple(self._supported_os)))
            self.logger.error(error_message)
            return False

    def _build_root(self):
        """  """
        self.logger.info("Building Root")
        vendor = ''
        model = ''
        os_version = ''
        sys_obj_id = self.snmp_handler.snmp_request(('SNMPv2-MIB', 'sysObjectID', 0))
        model_search = re.search(r'\.(?P<model>\d+$)', sys_obj_id)
        # if model_search:
        #     print "!!!!!!!", model_search.groupdict()
        #     vendor = model_search.groupdict()['vendor'].capitalize()
        #     model = model_search.groupdict()['model']

        sys_descr = self.snmp_handler.snmp_request(('SNMPv2-MIB', 'sysDescr', '0'))
        os_version_search = re.search('JUNOS \S+(,)?\s', sys_descr, re.IGNORECASE)
        if os_version_search:
            os_version = os_version_search.group(0).replace('JUNOS ', '').replace(',', '').strip(' \t\n\r')
        root_attributes = dict()
        root_attributes[RootAttributes.CONTACT_NAME] = self.snmp_handler.snmp_request(('SNMPv2-MIB', 'sysContact', '0'))
        root_attributes[RootAttributes.SYSTEM_NAME] = self.snmp_handler.snmp_request(('SNMPv2-MIB', 'sysName', '0'))
        root_attributes[RootAttributes.LOCATION] = self.snmp_handler.snmp_request(('SNMPv2-MIB', 'sysLocation', '0'))
        root_attributes[RootAttributes.OS_VERSION] = os_version
        root_attributes[RootAttributes.VENDOR] = vendor
        root_attributes[RootAttributes.MODEL] = model
        self._root.build_attributes(root_attributes)

    def _build_chassis(self):
        """ Get information about Chassis """
        self.logger.debug('Building Chassis')
        entity_table = self.snmp_handler.snmp_request(('ENTITY-MIB', 'entPhysicalTable'))
        for element_id, data in entity_table.iteritems():
            if data["entPhysicalClass"].replace("'", "") == "chassis":
                chassis = Chassis(element_id)
                chassis_attributes = dict()
                chassis_attributes[ChassisAttributes.MODEL] = data.get("entPhysicalModelName")
                chassis_attributes[ChassisAttributes.SERIAL_NUMBER] = data.get("entPhysicalSerialNum")
                chassis.build_attributes(chassis_attributes)
                self._root.chassis.append(chassis)
                self._chassis[element_id] = chassis

    def _build_power_modules(self):
        """ Get information about Power Port """
        self.logger.debug('Building PowerPorts')
        entity_table = self.snmp_handler.snmp_request(('ENTITY-MIB', 'entPhysicalTable'))
        for element_id, data in entity_table.iteritems():
            if data["entPhysicalClass"].replace("'", "") == "powerSupply":
                element_id = self._get_element_id(element_id)

                element = PowerPort(element_id)

                element_attributes = dict()
                element_attributes[PowerPortAttributes.MODEL] = data.get("entPhysicalModelName")
                element_attributes[PowerPortAttributes.PORT_DESCRIPTION] = data.get("entPhysicalDescr")
                element_attributes[PowerPortAttributes.SERIAL_NUMBER] = data.get("entPhysicalHardwareRev")
                element_attributes[PowerPortAttributes.VERSION] = data.get("entPhysicalSerialNum")
                element.build_attributes(element_attributes)

                chassis_id = int(entity_table[int(element_id)]['entPhysicalContainedIn'])
                if chassis_id in self._chassis:
                    chassis = self._chassis[chassis_id]
                    chassis.power_ports.append(element)

    def _build_modules(self):
        """ Get information about Modules """
        self.logger.debug('Building Modules')
        entity_table = self.snmp_handler.snmp_request(('ENTITY-MIB', 'entPhysicalTable'))
        for element_id, data in entity_table.iteritems():
            if data["entPhysicalClass"].replace("'", "") == "module":
                if self._is_sub_module(element_id):
                    continue
                element_id = self._get_element_id(element_id)
                element = Module(element_id)

                element_attributes = dict()
                element_attributes[ModuleAttributes.MODEL] = data.get("entPhysicalModelName")
                element_attributes[ModuleAttributes.SERIAL_NUMBER] = data.get("entPhysicalHardwareRev")
                element_attributes[ModuleAttributes.VERSION] = data.get("entPhysicalSerialNum")
                element.build_attributes(element_attributes)
                chassis_id = int(entity_table[int(element_id)]['entPhysicalContainedIn'])
                if chassis_id in self._chassis:
                    chassis = self._chassis[chassis_id]
                    chassis.modules.append(element)
                    self._modules[element_id] = element

    def _build_sub_modules(self):
        """ Get information about Sub Modules """
        self.logger.debug('Building Sub Modules')
        entity_table = self.snmp_handler.snmp_request(('ENTITY-MIB', 'entPhysicalTable'))
        for element_id, data in entity_table.iteritems():
            if data["entPhysicalClass"].replace("'", "") == "module":
                if self._is_sub_module(element_id):
                    element_id = self._get_element_id(element_id)
                    element = SubModule(element_id)

                    element_attributes = dict()
                    element_attributes[ModuleAttributes.MODEL] = data.get("entPhysicalModelName")
                    element_attributes[ModuleAttributes.SERIAL_NUMBER] = data.get("entPhysicalHardwareRev")
                    element_attributes[ModuleAttributes.VERSION] = data.get("entPhysicalSerialNum")
                    element.build_attributes(element_attributes)
                    module_id = int(entity_table[int(element_id)]['entPhysicalContainedIn'])
                    if module_id in self._modules:
                        module = self._modules[module_id]
                        module.modules.append(element)

    def _build_ports(self):
        """ Get information about Ports """
        if_table = self.snmp_handler.snmp_request(('IF-MIB', 'ifXTable'))
        for if_id, if_data in if_table.iteritems():
            pass

    def _log_autoload_details(self, autoload_details):
        self.logger.debug('-------------------- <RESOURCES> ----------------------')
        for resource in autoload_details.resources:
            self.logger.debug('{0}, {1}'.format(resource.relative_address, resource.name))
        self.logger.debug('-------------------- </RESOURCES> ----------------------')

        self.logger.debug('-------------------- <ATTRIBUTES> ---------------------')
        for attribute in autoload_details.attributes:
            self.logger.debug('-- {0}, {1}, {2}'.format(attribute.relative_address, attribute.attribute_name,
                                                        attribute.attribute_value))
        self.logger.debug('-------------------- </ATTRIBUTES> ---------------------')

    def discover(self):
        if not self._is_valid_device_os():
            raise Exception(self.__class__.__name__, 'Unsupported device OS')
        self._build_root()
        self._build_chassis()
        self._build_power_modules()
        self._build_modules()
        self._build_sub_modules()
        self._build_ports()
        autoload_details = self._root.get_autoload_details()
        # self._log_autoload_details(autoload_details)
        return autoload_details
