#!/usr/bin/python

import logging
import os
import re
import sys
from logging.handlers import RotatingFileHandler


class Logger(object):
    # log files location
    __LOG_DIRECTORY = "log"
    __DEBUG_LOG_FILENAME = __LOG_DIRECTORY + "/test_debug.log"
    __WARNING_LOG_FILENAME = __LOG_DIRECTORY + "/test.log"

    # log formatter
    __formatter = logging.Formatter(
        "#%(levelname)-8s [%(asctime)s] (%(process)d) %(module)s: %(message)s"
    )

    def __init__(self, d_e_b_u_g=False):
        # create log dir if not exists
        if not os.path.exists(self.__LOG_DIRECTORY):
            os.makedirs(self.__LOG_DIRECTORY)

        # log warnings to warning log file
        self.__rfh = RotatingFileHandler(
            self.__WARNING_LOG_FILENAME, maxBytes=1048576, backupCount=5
        )
        self.__rfh.setLevel(logging.INFO)
        self.__rfh.setFormatter(self.__formatter)

        # setting up logger with handlers
        self.mylogger = logging.getLogger("logger")
        self.mylogger.setLevel(logging.DEBUG)
        self.mylogger.addHandler(self.__rfh)

        if d_e_b_u_g:
            # log debug info to console
            self.__sh = logging.StreamHandler(sys.stdout)
            self.__sh.setLevel(logging.DEBUG)
            self.__sh.setFormatter(self.__formatter)

            # log debug info to debug log file
            self.__rfh2 = RotatingFileHandler(
                self.__DEBUG_LOG_FILENAME, maxBytes=1048576, backupCount=5
            )
            self.__rfh2.setLevel(logging.DEBUG)
            self.__rfh2.setFormatter(self.__formatter)

            self.mylogger.addHandler(self.__sh)
            self.mylogger.addHandler(self.__rfh2)
        else:
            pattern = "test_debug**"
            for f in os.listdir(self.__LOG_DIRECTORY):
                if re.search(pattern, f):
                    os.remove(os.path.join(self.__LOG_DIRECTORY, f))


# logger object and logging functions shortcut
logger = Logger(d_e_b_u_g=True)
debug = logger.mylogger.debug
info = logger.mylogger.info
warning = logger.mylogger.warning
error = logger.mylogger.error
critical = logger.mylogger.critical
