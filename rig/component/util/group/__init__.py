import json
import os
import sys

import rigkitten.rig.component.util as util
reload(util)

import build, guide
reload(build)
reload(guide)

PARAMFILE = "parms.json"
_DEFAULT_PARMS_ = {"name":{"value":__name__.rpartition(".")[2]},
                   "side":{"value":anim.kSideSuffix.CENTER},
                   "module":{"value":Rig.__module__}}

def new():
    if sys.platform == 'win32':
        rigfolder = os.path.dirname(__file__).replace("\\", "/")
        paramjson = "/".join([rigfolder, PARAMFILE])
    else:
        paramjson = "/".join([os.path.dirname(__file__), PARAMFILE])

    param_data = _DEFAULT_PARMS_
    with open(paramjson) as ofile: param_data.update(json.load(ofile))

    return Task(**param_data)


class Task(util.UtilComponent):

    _MODNAME = __name__

    def __init__(self, *arg, **kwargs):
        super(Task, self).__init__(*arg, **kwargs)

        # SET MAIN FUNCTIONS
        self._GUIDE_FNC = None
        self._RIG_FNC = None
