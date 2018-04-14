"""
This module contains handlers that will deal with incoming connections.
"""
from flask import request
from .config import SERVER_ADDRESS
from .utils import public_ip, log
from .exceptions import InvalidRequest
from .client import ResourceNotFound

def new_agent(client, data):
    """
    This handler is called when an agent checks in and does not have an existing session id.
    """
    log("Registering new agent")
    target_uuid = None
    facts = None

    try:
        target_uuid = data.get('uuid')
        facts = data.get('facts')

        # Enable Legacy Format Support
        if not target_uuid:
            facts = data.get('facts')
            mac_addrs = [interface['mac_addr'] for interface in data['facts']['interfaces']]
            target_uuid = ''.join(sorted(mac_addrs))
    except KeyError:
        raise InvalidRequest('LEGACY MODE: Missing required parameter.')

    config = data.get('config', {})
    servers = config.get('servers', [SERVER_ADDRESS if SERVER_ADDRESS else public_ip()])
    interval = config.get('interval', -1)
    interval_delta = config.get('interval_delta', -1)

    return client.create_session(
        target_uuid.lower(),
        servers,
        interval,
        interval_delta,
        config,
        facts)

def existing_agent(client, data):
    """
    This handler is called when an agent with a session id checks in.
    """
    session_id = data['session_id']

    resp = {
        'session_id': session_id
    }

    try:
        resp = client.session_checkin(
            session_id,
            data.get('responses'),
            data.get('config'),
            data.get('facts'),
            request.remote_addr,
        )
        resp['actions'] = [action.raw_json for action in resp['actions']]
    except ResourceNotFound:
        # If the session does not exist on the teamserver, reset the session
        resp['actions'] = [
            {
                'action_id': '0',
                'action_type': 999
            }
        ]

    return resp
