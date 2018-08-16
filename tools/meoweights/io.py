import json
import time
import logging

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oam

from . import skc, util
reload(skc)

logger = logging.getLogger(__name__)



def export(path, data, msg="Data Published"):

    with open(path, 'w') as outfile:
        json.dump(data, outfile)

    logger.info(msg)




def exportSkin(path, nodes=None, uvset="rigset"):
    kFileExtension = ".rkskin"

    if not nodes:
        selection = om.MGlobal.getActiveSelectionList()
        nodes = [selection.getDependNode(n) for n in
                 xrange(selection.length())]
        if not len(nodes): raise RuntimeError("No shape/transform selected")

    dataList = {}
    for e, node in enumerate(nodes):
        shape = util.getShape(node)
        skcobj = skc.SkinCluster(node, uvset)
        skcobj.gatherData()

        dataList.update(skcobj.data)

    print dataList

    # export
