#!/usr/bin/python
# -*- coding: utf-8 -*-

import utl
import argparse
import json
from DockerAPI import SwarmMaster
from DockerAPI import SwarmWorker


master = SwarmMaster()
worker = SwarmWorker()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', choices=['initSwarm', 'newService', 'joinSwarm', 'rmService', 'leaveSwarm', 'inspectTask'],
                        type=str, help='DynamicDockerSwarm action')
    parser.add_argument('--service', required=False, type=str, help='Service definition')
    parser.add_argument('--remote_addr', required=False, type=str, default=None, help='Remote address')
    parser.add_argument('--join_token', required=False, type=str, default=None, help='Docker Swarm join token.')
    parser.add_argument('--role', required=False, choices=['worker', 'master'], help='Worker/Master')
    parser.add_argument('--task_name', required=False, type=str, help='Specific task name')

    args = parser.parse_args()
    action = args.action
    serviceInfo = args.service
    remote_addr = args.remote_addr
    join_token = args.join_token

    if action == 'initSwarm':
        master.init_swarm(advertise_addr=utl.get_local_address())
        master.create_network(name='DynamicSwarmNetwork')
        master.get_join_token()
    elif action == 'joinSwarm':
        if not remote_addr or not join_token:
            print('Remote address and join_token must be specified together.')
        worker.join(remote_addr, join_token)
    elif action == 'newService':
        serviceInfo = serviceInfo.strip('\'')
        serviceInfo = json.loads(serviceInfo)
        master.create_service(serviceInfo)
    elif action == 'rmService':
        serviceName = serviceInfo
        master.rm_service(serviceName)
    elif action == 'leaveSwarm':
        role = args.role
        if role == 'worker':
            worker.leave()
        elif role == 'master':
            master.leave()
    elif action == 'inspectTask':
        task = args.task_name
        master.inspect_task(task)