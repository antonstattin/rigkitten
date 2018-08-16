import logging

class BaseComponent(object):

    def __init__(self, *args, **kwargs):
        # create objects standard arguments
        for key in kwargs: setattr(self, key, kwargs[key]["value"])

        

        self.logger = logging.getLogger(self._MODNAME)



    def log(self, msg):
        self.logger.info(msg)

    def build(self):
        self.log("Building Rig")
        self._RIG_FNC(self)

    def guide(self):
        self.log("Building Guide")
        self._GUIDE_FNC(self)
