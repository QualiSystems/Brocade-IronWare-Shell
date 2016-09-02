#!/usr/bin/python
# -*- coding: utf-8 -*-

import inject

from cloudshell.cli.command_template.command_template_service import add_templates, get_commands_list
from cloudshell.configuration.cloudshell_cli_binding_keys import CLI_SERVICE
from cloudshell.configuration.cloudshell_shell_core_binding_keys import LOGGER, CONTEXT, API
from cloudshell.networking.brocade.command_templates.vlan import VLAN_COMMANDS_TEMPLATES
from cloudshell.networking.operations.connectivity_operations import ConnectivityOperations
from cloudshell.networking.networking_utils import validateVlanNumber


class BrocadeConnectivityOperations(ConnectivityOperations):
    def __init__(self, context=None, api=None, cli_service=None, logger=None):
        self._context = context
        self._api = api
        self._cli_service = cli_service
        self._logger = logger

    @property
    def logger(self):
        return self._logger or inject.instance(LOGGER)

    @property
    def cli_service(self):
        return self._cli_service or inject.instance(CLI_SERVICE)

    @property
    def context(self):
        return self._context or inject.instance(CONTEXT)

    @property
    def api(self):
        return self._api or inject.instance(API)

    def add_vlan(self, vlan_range, port_list, port_mode, qnq=False, ctag=''):
        pass

    def remove_vlan(self, vlan_range, port_list, port_mode):
        pass

    @staticmethod
    def _load_vlan_command_templates():
        """ Load all required Commandtemplates to configure vlan on certain port """
        add_templates(VLAN_COMMANDS_TEMPLATES)

    def _get_vlan_list(self, vlan_str):
        """ Get VLAN list from inputted string

        :param vlan_str:
        :return list of VLANs or Exception
        """

        result = set()
        for splitted_vlan in vlan_str.split(","):
            if "-" not in splitted_vlan:
                if validateVlanNumber(splitted_vlan):
                    result.add(int(splitted_vlan))
                else:
                    raise Exception(self.__class__.__name__, "Wrong VLAN number detected {}".format(splitted_vlan))
            else:
                start, end = map(int, splitted_vlan.split("-"))
                if validateVlanNumber(start) and validateVlanNumber(end):
                    if start > end:
                        start, end = end, start
                    for vlan in range(start, end+1):
                        result.add(vlan)
                else:
                    raise Exception(self.__class__.__name__, "Wrong VLANs range detected {}".format(vlan_str))

        return list(result)

