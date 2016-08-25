#!/usr/bin/python
# -*- coding: utf-8 -*-

import cloudshell.networking.brocade.netiron.netiron_configuration as driver_config

from cloudshell.networking.brocade.netiron.autoload.netiron_snmp_autoload import NetIronSnmpAutoload as Autoload
from cloudshell.networking.brocade.brocade_send_command_operations import BrocadeSendCommandOperations as SendCommandOperations
from cloudshell.networking.brocade.netiron.handler.brocade_netiron_configuration_operations import BrocadeNetIronConfigurationOperations as ConfigurationOperations
from cloudshell.networking.brocade.netiron.netiron_driver_bootstrap import NetIronDriverBootstrap as DriverBootstrap
# from cloudshell.networking.brocade.ironware.handler.brocade_ironware_connectivity_operations import \
#     BrocadeIronwareConnectivityOperations as ConnectivityOperations

from cloudshell.networking.networking_resource_driver_interface_v4 import NetworkingResourceDriverInterface


from cloudshell.shell.core.context_utils import ContextFromArgsMeta
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface

SPLITTER = "-"*60


class BrocadeNetIronResourceDriver(ResourceDriverInterface, NetworkingResourceDriverInterface):
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

    # @property
    # def firmware_operations(self):
    #     return FirmwareOperations()

    @property
    def configuration_operations(self):
        return ConfigurationOperations()

    @property
    def send_command_operations(self):
        return SendCommandOperations()

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
        self.send_command_operations.logger.info("{splitter}\nRun method 'Send Custom Command' with parameters:\n"
                                                 "command = {command}\n{splitter}".format(splitter=SPLITTER,
                                                                                          command=custom_command))
        return self.send_command_operations.send_command(custom_command)

    def send_custom_config_command(self, context, custom_command):
        self.send_command_operations.logger.info("{splitter}\nRun method 'Send Custom Config Command' with parameters:"
                                                 "\ncommand = {command}\n{splitter}".format(splitter=SPLITTER,
                                                                                            command=custom_command))
        return self.send_command_operations.send_config_command(custom_command)

    # def load_firmware(self, context, path, vrf_management_name):
    #     self.firmware_operations.logger.info("{splitter}\nRun method 'Load Firmware' with parameters:\n"
    #                                          "path = {path},\n"
    #                                          "vrf_management_name = {vrf_management_name}\n"
    #                                          "{splitter}".format(splitter=SPLITTER,
    #                                                              path=path,
    #                                                              vrf_management_name=vrf_management_name))
    #     return self.firmware_operations.update_firmware(path, vrf_management_name)

    def save(self, context, configuration_type, folder_path, vrf_management_name=None):
        self.configuration_operations.logger.info("{splitter}\nRun method 'Save' with parameters:\n"
                                                  "configuration_type = {configuration_type},\n"
                                                  "folder_path = {folder_path},\n"
                                                  "{splitter}".format(splitter=SPLITTER,
                                                                      folder_path=folder_path,
                                                                      configuration_type=configuration_type))
        return self.configuration_operations.save_configuration(configuration_type, folder_path)

    def restore(self, context, path, configuration_type, restore_method, vrf_management_name=None):
        self.configuration_operations.logger.info("{splitter}\nRun method 'Restore' with parameters:"
                                                  "path = {path},\n"
                                                  "config_type = {config_type},\n"
                                                  "restore_method = {restore_method}\n"
                                                  "{splitter}".format(splitter=SPLITTER,
                                                                      path=path,
                                                                      config_type=configuration_type,
                                                                      restore_method=restore_method))
        return self.configuration_operations.restore_configuration(path, configuration_type, restore_method)

    def orchestration_save(self, context, mode="shallow", custom_params=None):
        pass

    def orchestration_restore(self, context, saved_artifact_info, custom_params=None):
        pass

    # def health_check(self, context):
    #     return self.operations.health_check()
    #
    # def shutdown(self, context):
    #     self.operations.shutdown()
