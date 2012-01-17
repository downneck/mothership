import logging
import os
MS_LOGDIR='/var/log/mothership/'

class MothershipCommon(object):
    def __init__(self):
        if not os.path.exists(MS_LOGDIR):
            os.mkdir(MS_LOGDIR)
        logging.basicConfig(filename=MS_LOGDIR+'mothership.log',level=logging.DEBUG)


    def debug(self,message):
        logging.debug(message)

    def warn(self,message):
        logging.warn(message)

    def info(self, message):
        logging.info(message)
