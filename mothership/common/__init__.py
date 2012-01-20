import logging
import os

MS_LOGDIR='/var/log/mothership/'

class MothershipCommon(object):
    def __init__(self):
        pass
    
    def check_min_num_args(self, len, min):
        return True
    def check_max_num_args(self, len, max):
        return True

    
class MothershipLogging(object):
    def __init__(self, cfg):
        if not os.path.exists(cfg.logdir):
            os.mkdir(cfg.logdir)
        if cfg.to_file:
            logging.basicConfig(filename=cfg.logdir+cfg.logfile,level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger()
        logger.setLevel(cfg.debug_level)

    def debug(self,message):
        logging.debug(message)

    def warn(self,message):
        logging.warn(message)

    def info(self, message):
        logging.info(message)
    
