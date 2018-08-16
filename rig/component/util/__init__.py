
import rigkitten.rig.component as cmpt

_DEFAULT_UTIL_PARMS_ = {"color":{"value":[20,20,20]},
                        "IsGroup":{"value":False}}

class UtilComponent(cmpt.BaseComponent):
    def __init__(self, *arg, **kwargs):

        for key in _DEFAULT_UTIL_PARMS_: setattr(self, key, kwargs[key]["value"])

        super(UtilComponent, self).__init__(*arg, **kwargs)
