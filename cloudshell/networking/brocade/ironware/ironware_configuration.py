#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
from collections import OrderedDict

from cloudshell.cli.session.session_creator import SessionCreator
from cloudshell.cli.session.session_proxy import ReturnToPoolProxy
from cloudshell.cli.session.telnet_session import TelnetSession
from cloudshell.configuration.cloudshell_cli_configuration import CONNECTION_TYPE_TELNET
from cloudshell.shell.core.context_utils import get_resource_address, get_attribute_by_name_wrapper
from cloudshell.shell.core.dependency_injection.context_based_logger import get_logger_with_thread_id
from cloudshell.snmp.quali_snmp_cached import QualiSnmpCached
from cloudshell.shell.core.context_utils import get_decrypted_password_by_attribute_name_wrapper


DEFAULT_PROMPT = r'[>%#]\s*$|[>%#]\s*\n'
ENABLE_PROMPT = r'#\s*$'
CONFIG_MODE_PROMPT = r'.*#\s*$'
ENTER_CONFIG_MODE_PROMPT_COMMAND = 'configure terminal'
EXIT_CONFIG_MODE_PROMPT_COMMAND = 'exit'
SUPPORTED_OS = ["IronWare"]


def enter_enable_mode(session):
    session.hardware_expect('enable', re_string=DEFAULT_PROMPT + '|' + ENABLE_PROMPT,
                            expect_map={'[Pp]assword': lambda session: session.send_line(
                                get_attribute_by_name_wrapper('Enable Password')())})
                                # get_decrypted_password_by_attribute_name_wrapper('Enable Password')())})
    result = session.hardware_expect('', re_string=r"{}|{}".format(DEFAULT_PROMPT, ENABLE_PROMPT))
    if not re.search(ENABLE_PROMPT, result):
        raise Exception('enter_enable_mode', 'Enable password is incorrect')

    return result


def send_default_actions(session):
    """Send default commands to configure/clear session outputs

    :return:
    """

    out = ''
    out += enter_enable_mode(session=session)
    out += session.hardware_expect('skip-page-display', ENABLE_PROMPT)
    out += session.hardware_expect(ENTER_CONFIG_MODE_PROMPT_COMMAND, CONFIG_MODE_PROMPT)
    out += session.hardware_expect('no logging console', CONFIG_MODE_PROMPT)
    out += session.hardware_expect('exit', r"{}|{}".format(DEFAULT_PROMPT, ENABLE_PROMPT))
    return out


def create_snmp_handler():
    kwargs = {}
    for key, value in QUALISNMP_INIT_PARAMS.iteritems():
        if callable(value):
            kwargs[key] = value()
        else:
            kwargs[key] = value
    return QualiSnmpCached(**kwargs)

DEFAULT_ACTIONS = send_default_actions

QUALISNMP_INIT_PARAMS = {'ip': get_resource_address,
                         'snmp_version': get_attribute_by_name_wrapper('SNMP Version'),
                         'snmp_user': get_attribute_by_name_wrapper('SNMP V3 User'),
                         'snmp_password': get_attribute_by_name_wrapper('SNMP V3 Password'),
                         'snmp_community': get_attribute_by_name_wrapper('SNMP Read Community'),
                         'snmp_private_key': get_attribute_by_name_wrapper('SNMP V3 Private Key')}


SNMP_HANDLER_FACTORY = create_snmp_handler

GET_LOGGER_FUNCTION = get_logger_with_thread_id

ERROR_MAP = OrderedDict(
    {r'[Ee]rror\s+saving\s+configuration': 'Save configuration error',
     r'syntax\s+error': 'Syntax error',
     r'[Uu]nknown\s+command': 'Unknown command',
     r'[Ee]rror\s+.+': 'Error'})


"""Definition for Telnet session"""
CONNECTION_MAP = OrderedDict()
telnet_session = SessionCreator(TelnetSession)
telnet_session.proxy = ReturnToPoolProxy
telnet_session.kwargs = {'username': get_attribute_by_name_wrapper('User'),
                         'password': get_attribute_by_name_wrapper('Password'),
                         'host': get_resource_address}
CONNECTION_MAP[CONNECTION_TYPE_TELNET] = telnet_session
