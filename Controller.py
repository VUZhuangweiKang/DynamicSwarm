#!/usr/bin/python
# -*- coding: utf-8 -*-

import utl
from DockerAPI import SwarmMaster


class Controller(object):
    def __init__(self):
        self.__swarm_master = SwarmMaster()

    def setup_cluster(self):
        # init swarm environment
        self.__swarm_master.init_swarm(advertise_addr=utl.get_local_address())

        # create network, this step is optional
        self.__swarm_master.create_network(name='DynamicSwarmNetwork')

    def add_service(self, service_json):
        self.__swarm_master.create_service(service_info=service_json)