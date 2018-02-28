# -*- encoding: utf-8 -*-
'''
Setup Mantra logging so all modules can do:

    from log import getlogger
    log = getlogger(__name__)
'''

import logging
import sys

TITLE = 'Mantra'


class MethodFilter(logging.Filter):
    'add classname to method names'
    # inspired by https://gist.github.com/techtonik/2151727

    def caller(self, module, funcname):
        'return full method/funcname where applicable'
        rv = funcname
        # search stack backwards to see if funcname is actually a method name
        frame = sys._getframe()
        while frame:
            if module == frame.f_globals.get('__name__', None):
                obj = frame.f_locals.get('self', None)
                if hasattr(obj, funcname):
                    classname = obj.__class__.__name__
                    rv = '{}.{}.{}'.format(module, classname, funcname)
                    break
            frame = frame.f_back

        del frame
        return rv

    def filter(self, record):
        'add class name to method name if applicable'
        record.funcName = self.caller(record.module, record.funcName)
        return True

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
    logr = logging.getLogger(name)
    logger.debug('created logger %s', logr.name)
    return logr
