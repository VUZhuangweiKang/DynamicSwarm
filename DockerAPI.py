#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import json
import docker
import traceback
import utl


class BaseDocker(object):
    def __init__(self):
        self.client = docker.from_env()
        self.logger = utl.get_logger('DockerLogger', 'DockerOperation.log')

    def pull_image(self, repository, tag):
        """
        Pull an image
        :param repository:
        :param tag:
        :return:
        """
        return self.client.images.pull(repository, tag)

    def create_container(self, container_info):
        assert type(container_info) is dict
        assert 'image' in container_info

        image = container_info['image']
        if 'command' in container_info:
            command = container_info['command']
            del container_info['command']
        else:
            command = None
        del container_info['image']

        try:
            result = self.client.containers.create(image, command, container_info)
            # if detach is specified, result is a container object, or it's STDOUT/STDERR
            if container_info['detach']:
                self.logger.info('Created container', result.id)
            return result
        except Exception as ex:
            self.logger.error(ex)

    def leave(self, force=True):
        """
        Leave a Swarm cluster
        :param force:
        :return:
        """
        self.client.swarm.leave(force)
        self.logger.info('Left swarm cluster.')

    def getNodeID(self):
        id_str = os.popen('docker info | grep NodeID').read()
        id_str = id_str.split(':')[1].strip()
        self.logger.info(id_str)


class SwarmMaster(BaseDocker):
    def __init__(self):
        super(SwarmMaster, self).__init__()
        self.__inited_flag = False
        self.__networks = []

    def init_swarm(self, advertise_addr):
        """
        Init Docker swarm environment
        :param advertise_addr: Externally reachable address advertised to other nodes.
        :return:
        """
        try:
            self.client.swarm.init(advertise_addr=advertise_addr)
            self.__inited_flag = True
            self.logger.info('Init Docker Swarm environment.')
        except Exception as ex:
            self.logger.error(ex)

    def create_service(self, service_info):
        """
        Create a service in swarm mode
        :param service_info:
        :type: dict
        :return:
        """
        try:
            # check input data and swarm environment
            assert type(service_info) is dict
            assert 'image' in service_info

            image = service_info['image']
            if 'command' in service_info:
                command = service_info['command']
                del service_info['command']
            else:
                command = None
            del service_info['image']

            # init EndpointSpec obj
            if 'endpoint_spec' in service_info:
                if 'ports' in service_info['endpoint_spec']:
                    ports = service_info['endpoint_spec']['ports']
                    temp = {}
                    for port in ports:
                        temp.update({int(port): int(service_info['endpoint_spec']['ports'][port])})
                    service_info['endpoint_spec']['ports'] = temp
                    service_info['endpoint_spec'] = docker.types.EndpointSpec(
                        mode=service_info['endpoint_spec']['mode'],
                        ports=service_info['endpoint_spec']['ports'])
                else:
                    service_info['endpoint_spec'] = docker.types.EndpointSpec(
                        mode=service_info['endpoint_spec']['mode'])

            # init ServiceMode obj
            if 'mode' in service_info:
                if service_info['mode']['service_mode'] == 'replicated':
                    service_info['mode'] = docker.types.ServiceMode(
                        mode='replicated',
                        replicas=int(service_info['mode']['replicas']))
                else:
                    service_info['mode'] = docker.types.ServiceMode(mode='global')

            # init Resources obj
            if 'resources' in service_info:
                cpu_limit = None
                mem_limit = None
                if 'mem_limit' in service_info['resources']:
                    mem_limit = service_info['resources']['mem_limit']
                if 'cpu_limit' in service_info['resources']:
                    cpu_limit = service_info['resources']['cpu_limit']
                service_info['resources'] = docker.types.Resources(cpu_limit=cpu_limit, mem_limit=mem_limit)

            service = self.client.services.create(image=image, command=command, **service_info)
            self.logger.info('%s' % service.id)

            return service
        except Exception as ex:
            self.logger.error(ex)
            traceback.print_exc()

    def rm_service(self, service_name=None, service_id=None):
        try:
            if service_id:
                for s in self.list_services():
                    if s.id == service_id:
                        s.remove()
            elif service_name:
                for s in self.list_services():
                    if s.name == service_name:
                        s.remove()
        except Exception as ex:
            self.logger.error(ex)

    def list_services(self):
        """
        :return: a list of services
        """
        return self.client.services.list()

    def get_join_token(self):
        """
        Get join token of a Swarm cluster
        :return: remote address, join_token
        """
        join_token = os.popen('sudo docker swarm join-token worker', 'r').read()
        print('Join token is here: %s' % join_token)
        return join_token

    def create_network(self, name, check_duplicate=True, subnet=None):
        """
        Create overlay and attachable network for a Swarm cluster
        :param name: network name
        :param check_duplicate: if do duplicate check
        :param subnet: subnet in CIDR format
        :return:
        """
        assert self.__inited_flag
        if subnet:
            ipam_pool = docker.types.IPAMPool(subnet=subnet)
            ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
        else:
            ipam_config = None
        network = self.client.networks.create(name=name,
                                              driver='overlay',
                                              attachable=True,
                                              check_duplicate=check_duplicate,
                                              ipam=ipam_config)
        self.logger.info('Created network %s' % network.id)
        self.__networks.append(network)
        return network

    def get_workers(self):
        """
        :return: a list of worker node objects
        """
        return self.client.nodes.list(filters={'role': 'manager'})

    def inspect_task(self, name):
        """
        Inspect task info
        :param name: task name
        :return: a json formatted string
        """
        services = self.list_services()
        for temp in services:
            if temp.name == name.split('.')[0]:
                taskInfo = temp.tasks(filters={'name': name})
                self.logger.info(taskInfo)

    def inspect_tasks(self, sv_name):
        """
        Inspect all tasks of a specific service
        :param sv_name: service name
        :return:
        """
        services = self.list_services()
        for sv in services:
            if sv.name == sv_name:
                self.logger.info(sv.tasks())
                return

    def list_nodes(self):
        """
        Get nodes id list
        :return:
        """
        nodes = self.client.nodes.list()
        ids = []
        for node in nodes:
            ids.append(node.id)
        self.logger.info(ids)

    def inspect_task_name(self, sv_name):
        """
        Get task id and task name
        :param sv_name:
        :return:
        """
        tasks = os.popen('sudo docker service ps %s | grep Running | awk \'{print $1 " " $2}\'' % sv_name).read().strip()
        self.logger.info(tasks)


class SwarmWorker(BaseDocker):
    def __init__(self):
        super(SwarmWorker, self).__init__()
        self.__joined_flag = False

    def join(self, remote_addr, join_token):
        """
        Add a new worker node into Swarm cluster
        :param remote_addr:
        :param join_token:
        :return:
        """
        assert not self.__joined_flag
        assert self.client.swarm.join(remote_addrs=[remote_addr], join_token=join_token)
        self.__joined_flag = True
        self.logger.info('Joined cluster as a worker node.')