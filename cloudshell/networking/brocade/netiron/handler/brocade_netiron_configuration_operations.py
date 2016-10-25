#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import time

from cloudshell.networking.networking_utils import UrlParser
from cloudshell.networking.brocade.brocade_configuration_operations import BrocadeConfigurationOperations


class BrocadeNetIronConfigurationOperations(BrocadeConfigurationOperations):
    def save(self, folder_path=None, configuration_type="running", vrf_management_name=None):
        """ Save device configuration to remote server

        :param folder_path: Full path to folder on remote server
        :param configuration_type: Type of configuration to save. Supports running and startup configuration

        :return Successful message or Exception
        """

        if not configuration_type:
            configuration_type = "running-config"
        elif "-config" not in configuration_type:
            configuration_type = configuration_type.lower() + "-config"

        if configuration_type not in ["running-config", "startup-config"]:
            raise Exception(self.__class__.__name__,
                            "Device doesn't support saving '{}' configuration type".format(configuration_type))

        folder_path = self.get_path(folder_path)

        if not folder_path.endswith("/"):
            folder_path += "/"

        file_name = "{0}-{1}-{2}".format(self.resource_name,
                                         configuration_type,
                                         time.strftime("%d%m%y-%H%M%S", time.localtime()))

        connection_dict = UrlParser.parse_url(folder_path)

        if connection_dict.get(UrlParser.PATH).endswith("/"):
            file_path = connection_dict.get(UrlParser.PATH) + file_name
        else:
            file_path = connection_dict.get(UrlParser.PATH) + "/" + file_name

        save_command = "copy {config} {scheme} {host} {file_path}".format(config=configuration_type,
                                                                          scheme=connection_dict.get(UrlParser.SCHEME),
                                                                          host=connection_dict.get(UrlParser.HOSTNAME),
                                                                          file_path=file_path)

        self.logger.info("Save configuration to file {0}".format(file_path))

        output = self.cli_service.send_command(command=save_command,
                                               expected_str=self._default_prompt)

        if re.search(r"TFTP.*done", output):
            return "{0}".format(file_name)
        else:
            matched = re.match(r"TFTP:.*", output)
            if matched:
                error = matched.group()
            else:
                error = "Error during copy configuration"
            raise Exception(self.__class__.__name__, "Save configuration failed with error: {}".format(error))

    def restore(self, path, configuration_type, restore_method='override', vrf_management_name=None):
        """ Restore configuration on device from remote server

        :param path: Full path to configuration file on remote server
        :param configuration_type: Type of configuration to restore. supports running and startup configuration
        :param restore_method: Type of restore method. Supports append and override. By default is override
        :param vrf_management_name: Not supported for Brocade Devices

        :return Successful message or Exception
        """

        _is_need_reload = False

        if not restore_method:
            restore_method = "override"

        if not configuration_type:
            configuration_type = "running-config"
        elif "-config" not in configuration_type:
            configuration_type = configuration_type.lower() + "-config"

        if configuration_type not in ["running-config", "startup-config"]:
            raise Exception(self.__class__.__name__,
                            "Device doesn't support restoring '{}' configuration type".format(configuration_type))

        connection_dict = UrlParser.parse_url(path)
        if connection_dict.get(UrlParser.PATH).endswith("/"):
            file_path = connection_dict.get(UrlParser.PATH) + connection_dict.get(UrlParser.FILENAME)
        else:
            file_path = connection_dict.get(UrlParser.PATH) + "/" + connection_dict.get(UrlParser.FILENAME)

        if configuration_type == "startup-config" and restore_method.lower() == "append":
            raise Exception(self.__class__.__name__,
                            "Device doesn't support restoring '{0}' configuration type with '{1}' method"
                            .format(configuration_type, restore_method))
        elif configuration_type == "running-config" and restore_method.lower() == "override":
            if self.session.session_type.lower() == 'console':
                restore_command = "copy {scheme} {config} {host} {file_path} overwrite"\
                    .format(scheme=connection_dict.get(UrlParser.SCHEME),
                            config=configuration_type,
                            host=connection_dict.get(UrlParser.HOSTNAME),
                            file_path=file_path)
            else:
                _is_need_reload = True
                configuration_type = "startup-config"
                restore_command = "copy {scheme} {config} {host} {file_path}" \
                    .format(scheme=connection_dict.get(UrlParser.SCHEME),
                            config=configuration_type,
                            host=connection_dict.get(UrlParser.HOSTNAME),
                            file_path=file_path)
        else:
            restore_command = "copy {scheme} {config} {host} {file_path}"\
                .format(scheme=connection_dict.get(UrlParser.SCHEME),
                        config=configuration_type,
                        host=connection_dict.get(UrlParser.HOSTNAME),
                        file_path=file_path)

        output = self.cli_service.send_command(command=restore_command,
                                               expected_str=self._default_prompt)

        if re.search(r"TFTP.*done", output):
            self.logger.debug("Reloading {} successfully".format(configuration_type))
            if _is_need_reload:
                self.state_operations.reload()
            return 'Restore configuration completed.'
        else:
            matched = re.match(r"TFTP:.*", output)
            if matched:
                error = matched.group()
            else:
                error = "Error during copy configuration"
            raise Exception(self.__class__.__name__, "Restore configuration failed with error: {}".format(error))
