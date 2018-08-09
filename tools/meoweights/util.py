import time
import logging

logger = logging.getLogger(__name__)

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oam

from rigkitten import rkattribute as rkattr


def removeNamespaceFromString(val):
    """ If name have a namespace, this func removes it

        :param val: string to remove namespace from
        :type val: str
    """
    tokens = val.split('|')
    result = ''
    for i, token in enumerate(tokens):
        if i > 0:
            result +="|"
        result += token.split(":")[-1]
    return result

def gatherCordinates(dagpath, uvset='rigset'):
    """ gathers uv and world space positions

        :param dagpath: dagpath object
        :type dagpath: MDagPath

        :return: list of ws positions, list of uv positions

    TODO: needs to add more then just MFnMesh
    """

    mfnMesh = om.MFnMesh(dagpath)

    points = mfnMesh.getPoints(om.MSpace.kWorld)
    wsPositions = []
    for point in points:
        wsPositions.append([point.x, point.y, point.z])

    availableUvSets = mfnMesh.getUVSetNames()
    uvPositions = []
    if uvset in availableUvSets:
        uvs = mfnMesh.getUVs(self.uvset)
        for i, u in enumerate(uvs[0]):
            v = uvs[1][i]
            uvPositions.append([u,v])

    return wsPositions, uvPositions

def getShape(node, intermediate=False):
    """ Returns the shape of given object or intermediate object

        :param node: dag node
        :type node: str / MObject

        :param intermediate: if we want to find the intermediate object of transform
        :type intermediate: bool
    """


    if isinstance(node, om.MObject):
        nodeDgPath = om.MDagPath().getAPathTo(node)
    else:
        mSel = om.MSelectionList()
        mSel.add(node)
        nodeDgPath = mSel.getDagPath(0)

    if nodeDgPath.apiType() == om.MFn.kTransform:

        shpnumb = nodeDgPath.numberOfShapesDirectlyBelow()
        for i in xrange(nodeDgPath.childCount()):
            childobj = nodeDgPath.child(i)
            if childobj.apiType() in [om.MFn.kMesh, om.MFn.kNurbsCurve,
                                      om.MFn.kNurbsSurface]:

                isInterObj = rkattr.getPlug(childobj, "intermediateObject").asBool()

                if intermediate and isInterObj:
                    return childobj
                elif not intermediate and not isInterObj:
                    return childobj

    elif nodeDgPath.apiType() in [om.MFn.kMesh, om.MFn.kNurbsCurve, om.MFn.kNurbsSurface]:
        return mSel.getDependNode(0)

    return None
