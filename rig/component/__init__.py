import traceback
import logging
import uuid
import sys

import maya.cmds as cmds

class kBuildType(object):
    PRE = "pre"
    RUN = "run"
    POST = "post"

class kStoreTypes(object):

    TRANSFROM = "transform"
    HIERARCHY = "hierarchy"

class BaseComponent(object):

    def __init__(self, *args, **kwargs):

        _DEFAULT_PARMS_ = {"parent":{ "value":None},
                           "id":{"value":str(uuid.uuid4()).split("-")[0]},
                           "name":{"value":"component"},
                           "stored":{"value":{}},
                           "stage":{"value":"init"}}

        # create objects standard arguments
        for key in _DEFAULT_PARMS_: setattr(self, key, _DEFAULT_PARMS_[key]["value"])
        for key in kwargs: setattr(self, key, kwargs[key]["value"])

        self._logger = logging.getLogger(self._MODNAME)

        # builders
        self._BUILD_MOD = None
        self._GUIDE_MOD = None

        self.kStoreTypes = kStoreTypes

    def log(self, msg):
        self._logger.info(msg)

    def build(self, bType=kBuildType.RUN):
        """ Run build methods

            :param bType: type of build
            :type bType: kBuildType
        """
        self._run(self._BUILD_MOD, bType)

    def guide(self, bType=kBuildType.RUN):
        """ Run guide methods

            :param bType: type of build
            :type bType: kBuildType
        """
        self._run(self._GUIDE_MOD, bType)

    def _run(self, mod, bType=kBuildType.RUN):
        """ runs the build methods """

        if not mod:
            self.log("id = {} | name = {} | method = SKIP!".format(self.id,
                                                                   self.name))
            return

        modname = mod.__name__.rpartition(".")[2]
        self.log("id = {} | name = {} | method = {}.{}".format(self.id, self.name,
                                                         modname, bType))

        # in case of crash save current stage
        currentStage = self.stage

        fnc = getattr(mod, bType)
        try:
            # turn on undo
            cmds.undoInfo(ock=True)
            self.stage =  "{}.{}".format(modname, bType)
            fnc(self)
        except Exception:

            # take care of crash...
            cmds.undoInfo(cck=True)
            cmds.undo()

            self.stage = currentStage
            raise



    def store(self, dtype, objects, **kwargs):
        kwargs.update({"objects":objects})
        if dtype not in self.stored.keys(): self.stored.update({dtype:[]})
        self.stored[dtype].append(kwargs)


    def serialize(self):
        """ serialize component so we can store it """

        #NOTE might have an issue if we have invalid objects inside list/dict..
        validTypes = [int, str, dict, list, float]

        data = {}
        for key, value in self.__dict__.items():
            for vtype in validTypes:
                if isinstance(value, vtype):
                    data.update({key:value})
                    break


        return data
