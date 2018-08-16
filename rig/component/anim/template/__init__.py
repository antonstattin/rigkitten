import json
import os
import sys

import rigkitten.rig.component.anim as anim
reload(anim)

import build, guide

PARAMFILE = "parms.json"

class Rig(anim.AnimRig):

    _MODNAME = __name__

    @classmethod
    def new(cls):

        if sys.platform == 'win32':
            rigfolder = os.path.dirname(__file__).replace("\\", "/")
            paramjson = "/".join([rigfolder, PARAMFILE])
        else:
            paramjson = "/".join([os.path.dirname(__file__), PARAMFILE])

        with open(paramjson) as ofile: param_data = json.load(ofile)

        return cls(**param_data)

    def __init__(self, *arg, **kwargs):
        super(Rig, self).__init__(*arg, **kwargs)

        # SET MAIN FUNCTIONS
        self._GUIDE_FNC = guide.guideIt
        self._RIG_FNC = build.rigIt


    def build(self):
        # RUN PRE
        super(Rig, self).build()
        # RUN POST


    def guide(self):
        # RUN PRE
        super(Rig, self).guide()
        # RUN POST
