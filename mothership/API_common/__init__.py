import logging
import os

MS_LOGDIR='/var/log/mothership/'

class MothershipCommon(object, filnename='mothership.log', debug_level='DEBUG'):
    def __init__(self):
        if not os.path.exists(MS_LOGDIR):
            os.mkdir(MS_LOGDIR)
        logging.basicConfig(filename=MS_LOGDIR+filename,level=logging.DEBUG)
        logging.setlevel(debug_level)

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
