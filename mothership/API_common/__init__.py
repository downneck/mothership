import logging
import os
MS_LOGDIR='/var/log/mothership/'

class MothershipCommon(object):
    def __init__(self):
        if not os.path.exists(MS_LOGDIR):
            os.mkdir(MS_LOGDIR)
        logging.basicConfig(filename=MS_LOGDIR+'mothership.log',level=logging.DEBUG)

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
