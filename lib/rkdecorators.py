from functools import wraps
import maya.cmds as cmds
from maya.api import OpenMaya as om
from .forked import apiundo


def enable_om_undo(fnc):
    """ enable undo for open Maya Commands, will need to return
        the MDGModifier as first object """

    @wraps(fnc)
    def _enable_om_undo(*args, **kwargs):

        ret = fnc(*args, **kwargs)

        if isinstance(ret, tuple):
            mod = ret[0]
            ret = [x for x in ret[1:]]
        else:
            mod = ret

        apiundo.commit(
            undo=mod.undoIt,
            redo=mod.doIt)

        return ret

    return _enable_om_undo
