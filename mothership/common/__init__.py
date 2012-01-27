import logging
import os
import sys

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

        # hello, little logger!
        logger = logging.getLogger()
        # set our level to DEBUG by default
        logger.setLevel(logging.DEBUG)
        # if we're asked to log to a file, set up both the file and the
        # stdout handlers and apply them to our logger
        if cfg.log_to_file:
            filehandler = logging.FileHandler(filename=cfg.logdir+'/'+cfg.logfile, mode='a')
            stdouthandler = logging.StreamHandler(sys.stdout)
            logger.addHandler(stdouthandler)
            logger.addHandler(filehandler)
        # if we're not asked to log to a file, just set up the stdout
        # handler and apply it to our logger
        else:
            stdouthandler = logging.StreamHandler(sys.stdout)
            logger.addHandler(stdouthandler)
        # set the default log level
        try:
            logger.setLevel(cfg.log_level)
        except:
            pass
        # let the world know we're alive
        print "wtf"
        logger.debug("logger initialized in %s" % (cfg.logdir+'/'+cfg.logfile))

    def change_log_level(self, level, logger='root'):
        """
        Change the logger level on the fly. Usually you want do that for replace
        the log level defined in the config file.
        """
        logger = logging.getLogger(logger)
        logger.setLevel(level)


    # Wrapper helper functions around the logger class
    def debug(self,message):
        logging.debug(message)

    def warn(self,message):
        logging.warn(message)

    def info(self, message):
        logging.info(message)
