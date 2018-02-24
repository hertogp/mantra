# -*- encoding: utf-8 -*-
'''
Setup Mantra logging so all modules can do:

    from log import getlogger
    log = getlogger(__name__)
'''

import logging
import inspect

TITLE = 'Mantra'

# format log records
# available also: %(filename)s, %(lineno)
msgfmt = '%(asctime)s %(name)-20s %(levelname)-8s %(funcName)10s: %(message)s'
datefmt = '%Y%m%d %H:%M:%S'
formatter = logging.Formatter(fmt=msgfmt, datefmt=datefmt)

logger = logging.getLogger(TITLE)                 # the root logger
logger.setLevel(logging.DEBUG)
# logger.addFilter(filter_)

fh = logging.FileHandler('{}.log'.format(TITLE))  # add filehandler
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()                      # add console handler
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)


def getlogger(*args):
    name = '.'.join([TITLE, '.'.join(args)])
    logger = logging.getLogger(name)
    return logger
