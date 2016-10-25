#!/usr/bin/python
# -*- coding: utf-8 -*-

import cloudshell.networking.brocade.netiron.netiron_configuration as driver_config

from cloudshell.networking.brocade.netiron.autoload.brocade_netiron_snmp_autoload import NetIronSnmpAutoload as Autoload
from cloudshell.networking.brocade.brocade_firmware_operations import BrocadeFirmwareOperations as FirmwareOperations
from cloudshell.networking.brocade.brocade_state_operations import BrocadeStateOperations as StateOperations
from cloudshell.networking.brocade.brocade_send_command_operations import BrocadeSendCommandOperations as SendCommandOperations
from cloudshell.networking.brocade.netiron.handler.brocade_netiron_configuration_operations import BrocadeNetIronConfigurationOperations as ConfigurationOperations
from cloudshell.networking.brocade.netiron.handler.brocade_netiron_connectivity_operations import BrocadeNetIronConnectivityOperations as ConnectivityOperations
from cloudshell.networking.networking_resource_driver_interface import NetworkingResourceDriverInterface
from cloudshell.shell.core.context_utils import ContextFromArgsMeta
from cloudshell.shell.core.driver_bootstrap import DriverBootstrap as Bootstrap
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface

SPLITTER = "-"*60


class BrocadeNetIronResourceDriver(ResourceDriverInterface, NetworkingResourceDriverInterface):
    __metaclass__ = ContextFromArgsMeta

    def __init__(self, config=None, connectivity_operations=None, send_command_operations=None, autoload=None):
        super(BrocadeNetIronResourceDriver, self).__init__()
        self.connectivity_operations = connectivity_operations
        self.send_command_operations = send_command_operations
        self.autoload = autoload
        bootstrap = Bootstrap()
        bootstrap.add_config(driver_config)
        if config:
            bootstrap.add_config(config)
        bootstrap.initialize()

    @property
    def _firmware_operations(self):
        return FirmwareOperations()

    @property
    def _autoload(self):
        return self.autoload or Autoload()

    @property
    def _send_command_operations(self):
        return self.send_command_operations or SendCommandOperations()

    @property
    def _configuration_operations(self):
        return ConfigurationOperations()

    @property
    def _connectivity_operations(self):
        return self.connectivity_operations or ConnectivityOperations()

    @property
    def _state_operations(self):
        return StateOperations()

    def initialize(self, context):
        pass

    def cleanup(self):
        pass

    def ApplyConnectivityChanges(self, context, request):
        self._connectivity_operations.logger.debug("Start applying connectivity changes, request is: {0}"
                                                   .format(str(request)))
        response = self._connectivity_operations.apply_connectivity_changes(request)

        self._connectivity_operations.logger.debug("Finished applying connectivity changes, response is: {0}"
                                                   .format(str(response)))
        return response

    def get_inventory(self, context):
        """ Get device structure with all standard attributes

        :return: AutoLoadDetails object
        """

        return self._autoload.discover()

    def run_custom_command(self, context, custom_command):
        """ Send custom command

        :param custom_command: command
        :return: command execution output
        """

        self._send_command_operations.logger.info("{splitter}\nRun method 'Send Custom Command' with parameters:\n"
                                                  "command = {command}\n{splitter}".format(splitter=SPLITTER,
                                                                                           command=custom_command))
        return self._send_command_operations.run_custom_command(custom_command)

    def run_custom_config_command(self, context, custom_command):
        """ Send custom command in configuration mode

        :param custom_command: command
        :return: command execution output
        """

        self._send_command_operations.logger.info("{splitter}\nRun method 'Send Custom Config Command' with parameters:"
                                                  "\ncommand = {command}\n{splitter}".format(splitter=SPLITTER,
                                                                                             command=custom_command))
        return self._send_command_operations.run_custom_config_command(custom_command)

    def send_custom_command(self, context, custom_command):
        """ Send custom command

        :param custom_command: command
        :return: command execution output
        """

        self._send_command_operations.logger.info("{splitter}\nRun method 'Send Custom Command' with parameters:\n"
                                                  "command = {command}\n{splitter}".format(splitter=SPLITTER,
                                                                                           command=custom_command))
        return self._send_command_operations.run_custom_command(custom_command)

    def send_custom_config_command(self, context, custom_command):
        """ Send custom command in configuration mode

        :param custom_command: command
        :return: command execution output
        """

        self._send_command_operations.logger.info("{splitter}\nRun method 'Send Custom Config Command' with parameters:"
                                                  "\ncommand = {command}\n{splitter}".format(splitter=SPLITTER,
                                                                                             command=custom_command))
        return self._send_command_operations.run_custom_config_command(custom_command)

    def load_firmware(self, context, path, vrf_management_name=None):
        """Upload and updates firmware on the resource
        :param path: full path to firmware file, i.e.tftp://10.10.10.1/firmware.bin
        :param vrf_management_name: VRF management Name
        :return: result
        """

        self._firmware_operations.logger.info("{splitter}\nRun method 'Load Firmware' with parameters:\n"
                                              "path = {path},\n"
                                              "vrf_management_name = {vrf_management_name}\n"
                                              "{splitter}".format(splitter=SPLITTER,
                                                                  path=path,
                                                                  vrf_management_name=vrf_management_name))
        return self._firmware_operations.load_firmware(path, vrf_management_name)

    def save(self, context, folder_path, configuration_type="running", vrf_management_name=None):
        """Save selected file to the provided destination

        :param configuration_type: source file, which will be saved
        :param folder_path: destination path where file will be saved
        :param vrf_management_name: VRF management Name
        :return saved configuration file name
        """

        if not configuration_type:
            configuration_type = "running"
        self._configuration_operations.logger.info("{splitter}\nRun method 'Save' with parameters:\n"
                                                   "configuration_type = {configuration_type},\n"
                                                   "folder_path = {folder_path},\n"
                                                   "{splitter}".format(splitter=SPLITTER,
                                                                       folder_path=folder_path,
                                                                       configuration_type=configuration_type))
        return self._configuration_operations.save(folder_path=folder_path, configuration_type=configuration_type)

    def restore(self, context, path, configuration_type="running", restore_method="override", vrf_management_name=None):
        """ Restore selected file to the provided destination

        :param path: source config file
        :param configuration_type: running or startup configs
        :param restore_method: append or override methods
        :param vrf_management_name: VRF management Name
        """

        if not configuration_type:
            configuration_type = 'running'

        if not restore_method:
            restore_method = 'override'

        self._configuration_operations.logger.info("{splitter}\nRun method 'Restore' with parameters:\n"
                                                   "path = {path},\n"
                                                   "config_type = {config_type},\n"
                                                   "restore_method = {restore_method}\n"
                                                   "{splitter}".format(splitter=SPLITTER,
                                                                       path=path,
                                                                       config_type=configuration_type,
                                                                       restore_method=restore_method))
        return self._configuration_operations.restore(path, configuration_type, restore_method)

    def orchestration_save(self, context, mode='shallow', custom_params=None):

        if not mode:
            mode = 'shallow'

        self._configuration_operations.logger.info("{splitter}\nRun method 'Orchestration save' with parameters:\n"
                                                   "mode = {mode},\n"
                                                   "custom_params = {custom_params}\n"
                                                   "{splitter}".format(splitter=SPLITTER,
                                                                       mode=mode,
                                                                       custom_params=custom_params))

        response = self._configuration_operations.orchestration_save(mode=mode, custom_params=custom_params)
        self._configuration_operations.logger.info("Orchestration save completed\n{splitter}".format(splitter=SPLITTER))
        return response

    def orchestration_restore(self, context, saved_artifact_info, custom_params=None):
        self._configuration_operations.logger.info("{splitter}\nRun method 'Orchestration restore'  with parameters:\n"
                                                   "saved_artifact_info = {saved_artifact_info},\n"
                                                   "custom_params = {custom_params}\n"
                                                   "{splitter}".format(splitter=SPLITTER,
                                                                       saved_artifact_info=saved_artifact_info,
                                                                       custom_params=custom_params))
        self._configuration_operations.orchestration_restore(saved_artifact_info=saved_artifact_info,
                                                             custom_params=custom_params)

        self._configuration_operations.logger.info("Orchestration restore completed\n{splitter}"
                                                   .format(splitter=SPLITTER))

    def health_check(self, context):
        """ Performs device health check """

        return self._state_operations.health_check()

    def shutdown(self, context):
        """ Shutdown device """
        self._state_operations.shutdown()
