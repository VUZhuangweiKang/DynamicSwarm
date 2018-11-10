#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging


def get_logger(logger_name, log_file, enable_stream=True):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    fl = logging.FileHandler(log_file)
    fl.setLevel(logging.DEBUG)

    cl = logging.StreamHandler()
    cl.setLevel(logging.DEBUG)

    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    fl.setFormatter(formatter)
    cl.setFormatter(formatter)

    logger.addHandler(fl)
    if enable_stream:
        logger.addHandler(cl)

    return logger