import json
import os
import sys

import rigkitten.rig.component.task as task
reload(task)

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

    return Rig(**param_data)


class Rig(task.TaskComponent):

    _MODNAME = __name__

    def __init__(self, *arg, **kwargs):
        super(Rig, self).__init__(*arg, **kwargs)

        # SET MAIN FUNCTIONS
        self._GUIDE_FNC = guide.rigIt
        self._RIG_FNC = build.rigIt

    def build(self):
        # RUN PRE
        build.preRigIt()

        super(Rig, self).build()
        # RUN POST


    def guide(self):
        # RUN PRE
        super(Rig, self).guide()
        # RUN POST
