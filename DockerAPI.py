#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import docker
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
            result = self.client.swarm.init(advertise_addr=advertise_addr)
            self.__inited_flag = True
            if result:
                self.logger.info('Init Docker Swarm environment.')
            else:
                self.logger.error('Something wrong while initializing Docker Swarm environment.')
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
            assert self.__inited_flag

            image = service_info['image']
            if 'command' in service_info:
                command = service_info['command']
                del service_info['command']
            else:
                command = None
            del service_info['image']

            # init EndpointSpec obj
            if 'endpoint_spec' in service_info:
                service_info['endpoint_spec'] = docker.types.EndpointSpec(mode=service_info['endpoint_spec']['mode'],
                                                                          ports=service_info['endpoint_spec']['ports'])

            # init ServiceMode obj
            if 'service_mode' in service_info:
                if service_info['service_mode']['mode'] == 'replicated':
                    service_info['service_mode'] = docker.types.ServiceMode(mode='replicated',
                                                                            replicas=service_info['service_mode']['replicas'])
                else:
                    service_info['service_mode'] = docker.types.ServiceMode(mode='global')

            # init Resources obj
            if 'resources' in service_info:
                cpu_limit = None
                mem_limit = None
                if 'mem_limit' in service_info['resources']:
                    mem_limit = service_info['resources']['mem_limit']
                if 'cpu_limit' in service_info['resources']:
                    cpu_limit = service_info['resources']['cpu_limit']
                service_info['resources'] = docker.types.Resources(cpu_limit=cpu_limit, mem_limit=mem_limit)

            service = self.client.services.create(image, command, service_info)

            self.logger.info('Created service:', service.id)

            return service
        except Exception as ex:
            self.logger.error(ex)

    def rm_service(self, service_id):
        assert type(service_id) is str
        try:
            for s in self.list_services():
                if s.id == service_id:
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
        remote_addr, join_token = os.popen('sudo docker swarm join-token worker | grep docker', 'r').read().strip().split()[4:]
        return remote_addr, join_token

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

    def leave(self, force=True):
        """
        Leave a Swarm cluster
        :param force:
        :return:
        """
        assert self.client.swarm.leave(force)
        self.logger.info('Left swarm cluster.')