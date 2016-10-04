#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

from cloudshell.networking.brocade.brocade_connectivity_operations import BrocadeConnectivityOperations
from cloudshell.networking.networking_utils import validateVlanNumber, validateVlanRange


class BrocadeNetIronConnectivityOperations(BrocadeConnectivityOperations):
    def __init__(self, context=None, api=None, cli_service=None, logger=None):
        BrocadeConnectivityOperations.__init__(self)
        self._context = context
        self._api = api
        self._cli_service = cli_service
        self._logger = logger

    def add_vlan(self, vlan_range, port, port_mode, qnq=False, ctag=''):
        """ Configure specified vlan range in specified switchport mode on provided port

        :param vlan_range: range of VLANs to be added
        :param port: interface Resource Full Address
        :param port_mode: type of adding VLAN ('trunk' or 'access')
        :param qnq: QNQ parameter for switchport mode dot1nq
        :param ctag: CTag details
        :return: success message or Exception
        """
        self.logger.info('VLANs Configuration Started')
        self.validate_vlan_methods_incoming_parameters(vlan_range, port, port_mode)
        if_name = self.get_port_name(port)

        for vlan in self._get_vlan_list(vlan_range):
            self.cli_service.send_config_command("vlan {}".format(vlan))

            if port_mode == "trunk":
                tag_type = "tagged"
            elif port_mode == "access":
                tag_type = "untagged"
            else:
                raise Exception(self.__class__.__name__,
                                "Unsupported port mode '{}'. Should be 'trunk' or 'access'".format(port_mode))

            res = self.cli_service.send_config_command("{tag_type} {if_name}".format(tag_type=tag_type, if_name=if_name))
            if re.search(r"error", res, re.IGNORECASE | re.DOTALL):
                raise Exception(self.__class__.__name__, "Error during vlan removing. See logs for details")

            if qnq and self._does_interface_support_qnq(if_name):
                self.cli_service.send_config_command("interface {if_name}".format(if_name=if_name))
                self.cli_service.send_config_command("tag-profile enable")

        self.cli_service.send_config_command("end")

        return "Vlan Configuration Completed"

    def remove_vlan(self, vlan_range, port, port_mode):
        """ Remove vlan from port

        :param vlan_range: range of VLANs to be deleted
        :param port: interface Resource Full Address
        :param port_mode: type of adding vlan ('trunk' or 'access')
        :return: success message or Exception
        """
        self.logger.info('VLANs Configuration Started')
        self.validate_vlan_methods_incoming_parameters(vlan_range, port, port_mode)
        if_name = self.get_port_name(port)

        for vlan in vlan_range.split(","):
            self.cli_service.send_config_command("interface {if_name}".format(if_name=if_name))

            if "-" in vlan:
                if len(vlan.split("-")) == 2 and validateVlanRange(vlan):
                    start, end = map(int, vlan.split("-"))
                    if start > end:
                        start, end = end, start

                    res = self.cli_service.send_config_command("remove-vlan vlan {start} to {end}".format(start=start,
                                                                                                          end=end))
                    if re.search(r"error", res, re.IGNORECASE | re.DOTALL):
                        raise Exception(self.__class__.__name__, "Error during vlan removing. See logs for details")
                else:
                    raise Exception(self.__class__.__name__, "Wrong VLAN range declaration'{}'.".format(vlan))
            else:
                if validateVlanNumber(vlan):
                    res = self.cli_service.send_config_command("remove-vlan vlan {}".format(vlan))
                    if re.search(r"error", res, re.IGNORECASE | re.DOTALL):
                        raise Exception(self.__class__.__name__, "Error during vlan removing. See logs for details")
                else:
                    raise Exception(self.__class__.__name__, "Wrong VLAN number '{}'.".format(vlan))

        self.cli_service.send_config_command("end")

        return "Remove Vlan Completed"

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
