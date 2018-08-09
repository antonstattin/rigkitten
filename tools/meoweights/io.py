import time
import logging

logger = logging.getLogger(__name__)

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oam

from rigkitten import rkattribute as rkattr


def removeNamespaceFromString(val):
    tokens = val.split('|')
    result = ''
    for i, token in enumerate(tokens):
        if i > 0:
            result +="|"
        result += token.split(":")[-1]
    return result

def gatherCordinates(dagpath, uvset='rigset'):
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


class SkinCluster(object):

    @staticmethod
    def getSkinCluster(oShape):
        """ returns a MfnSkinCluster if it exists on the passed shape

            Note: might not work if there is a blendshape with a mesh
                  that is connected to a skincluster..

            :param oShape: the shape
            :type oShape: MObject
        """

        try:
            itDG = om.MItDependencyGraph(oShape, om.MFn.kSkinClusterFilter, om.MItDependencyGraph.kUpstream)
            while not itDG.isDone():
                oCurrentItem = itDG.currentNode()
                fnSkin = oam.MFnSkinCluster(oCurrentItem)

                # Don't need to loop any more since we got the skin cluster
                break
            return fnSkin
        except:
            raise RuntimeError("No skincluster on '{}'".format(om.MFnDependencyNode(oShape).name()))

    def __init__(self, shape=None, uvset="rigset"):



        if not shape:
            selection = om.MGlobal.getActiveSelectionList()
            if not selection.length(): raise RuntimeError("No shape/transform selected")
            shape = selection.getDependNode(0)

        self.shape = getShape(shape)
        if not self.shape:
            raise RuntimeError("No shapes connected to selected/passed shape")

        # set uv set
        self.uvset = uvset

        # get MFnSkinCluster and skinclusters name
        self.skcNode = SkinCluster.getSkinCluster(self.shape)
        self.skcName = om.MFnDependencyNode(self.skcNode.object()).name()

        self.data = {
                    'weights':{},
                    'blendWeights':[],
                    'wsPos':[],
                    'uv':[],
                    'name':self.skcName
                    }

    def gatherData(self):
        # start timer
        start = time.clock()

        dagpath, cmpnts = self._getComponents()
        self.gatherInfWeights(dagpath, cmpnts)
        self.gatherBlendWeights(dagpath, cmpnts)

        # gather worldPosition and UVs (if rigset exists)
        wsPositions, uvPositions = gatherCordinates(dagpath, uvset=self.uvset)
        self.data["wsPos"] = wsPositions
        self.data["uv"] = uvPositions

        for attr in ['skinningMethod', 'normalizeWeights']:
            self.data[attr] = rkattr.getPlug(self.skcNode.object(), attr).asInt()

        # end timer
        elapsed = time.clock()
        elapsed = elapsed - start

        logger.info("Exported Data in {}s".format(elapsed))


    def gatherBlendWeights(self, dagpath, cmpnts):

        weights = self.skcNode.getBlendWeights(dagpath, cmpnts)
        self.data['blendWeights'] = [weight for weight in weights]

    def gatherInfWeights(self, dagpath, cmpnts):
        weights = self._getCurrentWeights(dagpath, cmpnts)

        infPaths = self.skcNode.influenceObjects()
        numInfpercomp = len(weights)/(len(infPaths))

        for i, infPath in enumerate(infPaths):
            influenceName = infPath.partialPathName()
            infCleanName = removeNamespaceFromString(influenceName)

            self.data['weights'][infCleanName] = \
                [weights[jj*(len(infPaths)-1)*i] for jj in range(numInfpercomp)]

    def _getCurrentWeights(self, dagpath, cmpnts):
        weightArray, infnumb = self.skcNode.getWeights(dagpath, cmpnts)

        return weightArray

    def _getComponents(self):
        fnset = om.MFnSet(self.skcNode.deformerSet)

        members = fnset.getMembers(False)
        dagpath = members.getDagPath(0)
        components = members.getComponent(0)[1]

        return dagpath, components
