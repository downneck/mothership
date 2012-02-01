import os
import sys
import logging

class MothershipCommon(object):
    """
    Common methods utilised by most mothership module
    """
    def __init__(self):
        pass

    def check_min_num_args(self, len, min):
        return True
    def check_max_num_args(self, len, max):
        return True

class MothershipLogger(object):
    """
    Mothership logger class
    """
    def __init__(self, cfg):
        if not os.path.exists(cfg.logdir):
            os.mkdir(cfg.logdir)

        # create a new logger to not conflict with any logging instance
        logger = logging.getLogger('mothership')

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # if we're asked to log to a file, set up both the file and the
        # stdout handlers and apply them to our logger

        if cfg.log_to_file:
            filehandler = logging.FileHandler(filename=cfg.logdir+'/'+cfg.logfile, mode='a')
            filehandler.setFormatter(formatter)
            logger.addHandler(filehandler)

        # if we're not asked to log to a file, just set up the stdout
        # and stderr handlers and apply them to our logger
        stdouthandler = logging.StreamHandler(sys.stdout)
        stdouthandler.setFormatter(formatter)
        logger.addHandler(stdouthandler)

        # set the default log level
        try:
            level = getattr(logging, cfg.log_level.upper())
            logger.setLevel(level)
        except:
            logger.setLevel(logging.DEBUG)

        logger.debug("logger initialized in %s" % (cfg.logdir+'/'+cfg.logfile))

        self.logger = logger


    # to change the logger log level
    def change_log_level(self, level, logger='mothership'):
        """
        Change the logger level on the fly. Usually you want do that for replace
        the log level defined in the config file.
        """
        logger = logging.getLogger(logger)
        logger.setLevel(level)


    # Wrapper helper functions around the logger class
    def debug(self, message):
        self.logger.debug(message)

    def warn(self, message):
        self.logger.warn(message)

    def info(self, message):
        self.logger.info(message)
