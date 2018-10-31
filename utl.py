#!/usr/bin/env /usr/local/bin/python
# encoding: utf-8
# Author: Zhuangwei Kang


import socket
import re
import logging
import cpuinfo
import psutil


def get_logger(logger_name, log_file):
    '''
    Generate a logger object
    :param logger_name:
    :param log_file:
    :return: logger obj
    '''
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    fl = logging.FileHandler(log_file)
    fl.setLevel(logging.DEBUG)

    cl = logging.StreamHandler()
    cl.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fl.setFormatter(formatter)
    cl.setFormatter(formatter)

    logger.addHandler(fl)
    logger.addHandler(cl)

    return logger


def ip_is_local(ip_string):
    """
    Uses a regex to determine if the input ip is on a local network. Returns a boolean.
    It's safe here, but never use a regex for IP verification if from a potentially dangerous source.
    """
    combined_regex = "(^10\.)|(^172\.1[6-9]\.)|(^172\.2[0-9]\.)|(^172\.3[0-1]\.)|(^192\.168\.)"
    return re.match(combined_regex, ip_string) is not None # is not None is just a sneaky way of converting to a boolean


# get local ip address of a server
def get_local_address():
    # socket.getaddrinfo returns a bunch of info, so we just get the IPs it returns with this list comprehension.
    local_ips = [x[4][0] for x in socket.getaddrinfo(socket.gethostname(), 80)
                 if ip_is_local(x[4][0])]

    # select the first IP, if there is one.
    local_ip = local_ips[0] if len(local_ips) > 0 else None

    # If the previous method didn't find anything, use this less desirable method that lets your OS figure out which
    # interface to use.
    if not local_ip:
        # create a standard UDP socket ( SOCK_DGRAM is UDP, SOCK_STREAM is TCP )
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Open a connection to one of Google's DNS servers. Preferably change this to a server in your control.
            temp_socket.connect(('8.8.8.8', 9))
            # Get the interface used by the socket.
            local_ip = temp_socket.getsockname()[0]
        except socket.error:
            # Only return 127.0.0.1 if nothing else has been found.
            local_ip = "127.0.0.1"
        finally:
            # Always dispose of sockets when you're done!
            temp_socket.close()
    return local_ip


def get_total_cores():
    cores_num = psutil.cpu_count()
    print('Total core number is %d' % cores_num)
    return cores_num


def get_total_mem():
    # get free memory
    memfree = str(psutil.virtual_memory()[4]) + 'k'
    return str(memory_size_translator(memfree)) + 'm'


# convert memory size to mB
def memory_size_translator(mem_size):
    # '''
    # :param mem_size: b/k/m/g
    # :return: mem_size: m
    # '''
    # remove 'B' and blank from input str
    mem_size = mem_size.replace(' ', '')
    mem_size = mem_size.replace('B', '')
    num = float(re.findall(r"\d+\.?\d*", mem_size)[0])
    unit = mem_size[-1]
    return {
        'm': num,
        'k': num / 1000,
        'b': num / 1000 / 1000,
        'g': num * 1000
    }.get(unit)