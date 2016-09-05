#!/usr/bin/python
# -*- coding: utf-8 -*-

import cloudshell.networking.brocade.netiron.netiron_configuration as driver_config

from cloudshell.networking.brocade.netiron.autoload.brocade_netiron_snmp_autoload import NetIronSnmpAutoload as Autoload
from cloudshell.networking.brocade.brocade_firmware_operations import BrocadeFirmwareOperations as FirmwareOperations
from cloudshell.networking.brocade.brocade_state_operations import BrocadeStateOperations as StateOperations
from cloudshell.networking.brocade.brocade_send_command_operations import BrocadeSendCommandOperations as SendCommandOperations
from cloudshell.networking.brocade.netiron.handler.brocade_netiron_configuration_operations import BrocadeNetIronConfigurationOperations as ConfigurationOperations
# from cloudshell.networking.generic_bootstrap import NetworkingGenericBootstrap as Bootstrap
from cloudshell.networking.brocade.netiron.netiron_driver_bootstrap import NetIronDriverBootstrap as Bootstrap
from cloudshell.networking.brocade.brocade_connectivity_operations import BrocadeConnectivityOperations as ConnectivityOperations

from cloudshell.networking.networking_resource_driver_interface import NetworkingResourceDriverInterface


from cloudshell.shell.core.context_utils import ContextFromArgsMeta
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface

SPLITTER = "-"*60


class BrocadeNetIronResourceDriver(ResourceDriverInterface, NetworkingResourceDriverInterface):
    __metaclass__ = ContextFromArgsMeta

    def __init__(self, config=None, connectivity_operations=None, send_command_operations=None, autoload=None):
        super(BrocadeNetIronResourceDriver, self).__init__()
        self._connectivity_operations = connectivity_operations
        self._send_command_operations = send_command_operations
        self._autoload = autoload
        bootstrap = Bootstrap()
        bootstrap.add_config(driver_config)
        if config:
            bootstrap.add_config(config)
        bootstrap.initialize()

    @property
    def firmware_operations(self):
        return FirmwareOperations()

    @property
    def autoload(self):
        return self._autoload or Autoload()

    @property
    def send_command_operations(self):
        return self._send_command_operations or SendCommandOperations()

    @property
    def configuration_operations(self):
        return ConfigurationOperations()

    @property
    def connectivity_operations(self):
        return self._connectivity_operations or ConnectivityOperations()

    @property
    def state_operations(self):
        return StateOperations()

    def initialize(self, context):
        pass

    def cleanup(self):
        pass

    def ApplyConnectivityChanges(self, context, request):
        return self.connectivity_operations.apply_connectivity_changes(request)

    def get_inventory(self, context):
        """ Get device structure with all standard attributes

        :return: AutoLoadDetails object
        """

        return self.autoload.discover()

    def send_custom_command(self, context, custom_command):
        """ Send custom command

        :param custom_command: command
        :return: command execution output
        """

        self.send_command_operations.logger.info("{splitter}\nRun method 'Send Custom Command' with parameters:\n"
                                                 "command = {command}\n{splitter}".format(splitter=SPLITTER,
                                                                                          command=custom_command))
        return self.send_command_operations.send_command(custom_command)

    def send_custom_config_command(self, context, custom_command):
        """ Send custom command in configuration mode

        :param custom_command: command
        :return: command execution output
        """

        self.send_command_operations.logger.info("{splitter}\nRun method 'Send Custom Config Command' with parameters:"
                                                 "\ncommand = {command}\n{splitter}".format(splitter=SPLITTER,
                                                                                            command=custom_command))
        return self.send_command_operations.send_config_command(custom_command)

    def load_firmware(self, context, path, vrf_management_name=None):
        """Upload and updates firmware on the resource
        :param path: full path to firmware file, i.e.tftp://10.10.10.1/firmware.bin
        :param vrf_management_name: VRF management Name
        :return: result
        """

        self.firmware_operations.logger.info("{splitter}\nRun method 'Load Firmware' with parameters:\n"
                                             "path = {path},\n"
                                             "vrf_management_name = {vrf_management_name}\n"
                                             "{splitter}".format(splitter=SPLITTER,
                                                                 path=path,
                                                                 vrf_management_name=vrf_management_name))
        return self.firmware_operations.load_firmware(path, vrf_management_name)

    def save(self, context, configuration_type, folder_path, vrf_management_name=None):
        """Save selected file to the provided destination
        :param configuration_type: source file, which will be saved
        :param folder_path: destination path where file will be saved
        :param vrf_management_name: VRF management Name
        :return saved configuration file name
        """

        self.configuration_operations.logger.info("{splitter}\nRun method 'Save' with parameters:\n"
                                                  "configuration_type = {configuration_type},\n"
                                                  "folder_path = {folder_path},\n"
                                                  "{splitter}".format(splitter=SPLITTER,
                                                                      folder_path=folder_path,
                                                                      configuration_type=configuration_type))
        return self.configuration_operations.save(configuration_type, folder_path)

    def restore(self, context, path, configuration_type='running', restore_method='override', vrf_management_name=None):
        """ Restore selected file to the provided destination

        :param path: source config file
        :param configuration_type: running or startup configs
        :param restore_method: append or override methods
        :param vrf_management_name: VRF management Name
        """
        self.configuration_operations.logger.info("{splitter}\nRun method 'Restore' with parameters:"
                                                  "path = {path},\n"
                                                  "config_type = {config_type},\n"
                                                  "restore_method = {restore_method}\n"
                                                  "{splitter}".format(splitter=SPLITTER,
                                                                      path=path,
                                                                      config_type=configuration_type,
                                                                      restore_method=restore_method))
        return self.configuration_operations.restore(path, configuration_type, restore_method)

    def orchestration_save(self, context, mode="shallow", custom_params=None):
        self.configuration_operations.logger.info("{splitter}\nOrchestration save started".format(splitter=SPLITTER))

        response = self.configuration_operations.orchestration_save(mode=mode, custom_params=custom_params)
        self.configuration_operations.logger.info("Orchestration save completed\n{}".format(splitter=SPLITTER))
        return response

    def orchestration_restore(self, context, saved_artifact_info, custom_params=None):
        self.configuration_operations.logger.info("{splitter}\nOrchestration restore started".format(splitter=SPLITTER))
        self.configuration_operations.orchestration_restore(saved_artifact_info=saved_artifact_info,
                                                            custom_params=custom_params)

        self.configuration_operations.logger.info("Orchestration restore completed\n{}".format(splitter=SPLITTER))

    def health_check(self, context):
        """ Performs device health check """

        return self.state_operations.health_check()

    def shutdown(self, context):
        """ Shutdown device """
        self.state_operations.shutdown()