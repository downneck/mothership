import logging
import os

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

        if cfg.log_to_file:
            logging.basicConfig(filename=cfg.logdir+'/'+cfg.logfile,level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.DEBUG)
        # set the default log level 
        logger = logging.getLogger()
        logger.setLevel(cfg.debug_level)

    def change_log_level(self, logger='root', level):
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
