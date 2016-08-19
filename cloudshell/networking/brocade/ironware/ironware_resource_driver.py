#!/usr/bin/python
# -*- coding: utf-8 -*-

import cloudshell.networking.brocade.ironware.ironware_configuration as driver_config

from cloudshell.networking.brocade.autoload.brocade_snmp_autoload import BrocadeSnmpAutoload as Autoload
from cloudshell.networking.brocade.brocade_ironware_operations import BrocadeIronWareOperations as Operations
from cloudshell.networking.brocade.ironware.ironware_driver_bootstrap import IronWareDriverBootstrap as DriverBootstrap

from cloudshell.networking.networking_resource_driver_interface_v4 import NetworkingResourceDriverInterface
# from cloudshell.networking.brocade.ironware.handler.brocade_ironware_connectivity_operations import \
#     BrocadeIronwareConnectivityOperations as ConnectivityOperations

from cloudshell.shell.core.context_utils import ContextFromArgsMeta
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface


class IronWareResourceDriver(ResourceDriverInterface, NetworkingResourceDriverInterface):
    __metaclass__ = ContextFromArgsMeta

    def __init__(self, config=None):
        bootstrap = DriverBootstrap()
        bootstrap.add_config(driver_config)
        if config:
            bootstrap.add_config(config)
        bootstrap.initialize()

    # @property
    # def connectivity_operations(self):
    #     return ConnectivityOperations()

    @property
    def operations(self):
        return Operations()

    @property
    def autoload(self):
        return Autoload()

    def initialize(self, context):
        pass

    def cleanup(self):
        pass

    # def ApplyConnectivityChanges(self, context, request):
    #     return self.connectivity_operations.apply_connectivity_changes(request)

    def get_inventory(self, context):
        return self.autoload.discover()

    def send_custom_command(self, context, custom_command):
        return self.operations.send_command(custom_command)

    def send_custom_config_command(self, context, custom_command):
        return self.operations.send_config_command(custom_command)

    def load_firmware(self, context, remote_host, file_path):
        return self.operations.update_firmware(remote_host, file_path)

    def save(self, context, folder_path, configuration_type, vrf_management_name=None):
        self.operations.save_configuration(folder_path, configuration_type)

    def restore(self, context, path, configuration_type, restore_method, vrf_management_name=None):
        return self.operations.restore_configuration(path, configuration_type, restore_method)

    def health_check(self, context):
        return self.operations.health_check()

    def orchestration_save(self, context, mode="shallow", custom_params=None):
        pass

    def orchestration_restore(self, context, saved_artifact_info, custom_params=None):
        pass

    def shutdown(self, context):
        self.operations.shutdown()
