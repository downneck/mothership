import logging
import os

MS_LOGDIR='/var/log/mothership/'

class MothershipCommon(object):
    def __init__(self, logfile='motherhship.log', debug_level='DEBUG', to_file=True):
        if not os.path.exists(MS_LOGDIR):
            os.mkdir(MS_LOGDIR)
        if to_file:
            logging.basicConfig(filename=MS_LOGDIR+logfile,level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger()
        logger.setLevel(debug_level)

    def check_min_num_args(self, len, min):
        return True
    def check_max_num_args(self, len, max):
        return True

    def debug(self,message):
        logging.debug(message)

    def warn(self,message):
        logging.warn(message)

    def info(self, message):
        logging.info(message)
