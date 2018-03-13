# -*- encoding: utf-8 -*-
'''
Setup Mantra logging so all modules can do:

    from log import getlogger
    log = getlogger(__name__)
'''

import logging
import logging.handlers
import sys

# App imports
from config import cfg


class ThreadFilter(logging.Filter):
    'qparse.py filter to limit logging to a specific compile job-id == test_id'
    def __init__(self, threadname=None):
        self.threadname = threadname

    def filter(self, record):
        if record.threadName == self.threadname:
            return True
        return False


class MethodFilter(logging.Filter):
    'adds classname to method names, if any'
    # Notes:
    # - inspired by https://gist.github.com/techtonik/2151727
    # - assumption: traversing stack backwards, caller is 1st obj which has
    #   funcName as a (callable) attribute

    def caller(self, module, funcname):
        'return full method/funcname where applicable'
        rv = '.'.join([module, funcname])
        # search stack backwards to see if funcname is actually a method name
        frame = sys._getframe()
        while frame:
            if module == frame.f_globals.get('__name__', None):
                obj = frame.f_locals.get('self', None)
                method = getattr(obj, funcname, None)
                if method and callable(method):
                    classname = obj.__class__.__name__
                    rv = '.'.join([module, classname, funcname])
                    break
            frame = frame.f_back

        del frame
        rv = '{}()'.format(rv) if not rv.endswith('>') else rv
        return rv

    def filter(self, record):
        'add class name to method name if applicable'
        record.funcName = self.caller(record.module, record.funcName)
        return True


def setup(app_name, log_file):
    'setup app global logger plus handlers'
    msgfmt = ('%(asctime)s %(name)s [%(threadName)s | '
              '%(levelname)s] %(funcName)10s: %(message)s'
              )
    datefmt = '%Y%m%d %H:%M:%S'
    formatter = logging.Formatter(fmt=msgfmt, datefmt=datefmt)

    # the root logger

    logger = logging.getLogger(app_name)
    logger.setLevel(logging.DEBUG)
    logger.addFilter(MethodFilter())

    # root filehandler

    fh = logging.handlers.RotatingFileHandler(log_file, 1024*1024, 3)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    # fh.addFilter(MethodFilter())
    logger.addHandler(fh)

    # root console handler

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    # ch.addFilter(MethodFilter())
    logger.addHandler(ch)

    logger.debug('created root logger {}'.format(logger.name))


def getlogger(*args):
    name = '.'.join([cfg.app_name, '.'.join(args)])
    logr = logging.getLogger(name)
    return logr
