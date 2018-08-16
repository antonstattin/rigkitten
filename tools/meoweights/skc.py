import time
import logging

logger = logging.getLogger(__name__)

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oam

# creating the skc + bindpose + deformer set is to messy..
import maya.cmds as cmds

from rigkitten import rkattribute as rkattr
from . import util, io

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

    def importWeights(data, type="topology", **kwarg):

        self.data = data
        if type == "topology":
            self._importWeightTopo(**kwarg)
        elif type == "worldspace":
            self._importWeightWS(**kwarg)
        elif type == "uv":
            self._importWeightUV(**kwarg)

    def _importWeightWS(self, **kwarg): return
    def _importWeightUV(self, **kwarg): return

    def _importWeightTopo(self, **kwarg):

        shape = kwarg.get("shape", "none")

        key = self.data.keys()[0]
        if not shape: shape = key

        influences = self.data[key]["weights"].keys()
        nw = self.data[key]["normalizeWeights"].keys()
        sm = self.data[key]["skinningMethod"].keys()
        skc = cmds.skinCluster(influences, shape, nw=nw)

        skcMObj = util.getMObj(skc)
        fnSkin = oam.MFnSkinCluster(skcMObj)

    def __init__(self, shape=None, uvset="rigset"):

        if not shape:
            selection = om.MGlobal.getActiveSelectionList()
            if not selection.length(): raise RuntimeError("No shape/transform selected")
            shape = selection.getDependNode(0)

        self.shape = util.getShape(shape)
        if not self.shape:
            raise RuntimeError("No shapes connected to selected/passed shape")

        # set uv set
        self.uvset = uvset

        # get MFnSkinCluster and skinclusters name
        self.skcNode = SkinCluster.getSkinCluster(self.shape)
        self.skcName = om.MFnDependencyNode(self.skcNode.object()).name()

        self.shapeName = om.MFnDependencyNode(self.shape).name()

        self.data = {self.shapeName:{
                                    'weights':{},
                                    'blendWeights':[],
                                    'wsPos':[],
                                    'uv':[],
                                    'name':self.skcName
                                    }}

    def gatherData(self):
        """ gathers all the skincluster-data """

        dagpath, cmpnts = self._getComponents()
        self.gatherInfWeights(dagpath, cmpnts)
        self.gatherBlendWeights(dagpath, cmpnts)

        # gather worldPosition and UVs (if rigset exists)
        wsPositions, uvPositions = util.gatherCordinates(dagpath, uvset=self.uvset)
        self.data[self.shapeName]["wsPos"] = wsPositions
        self.data[self.shapeName]["uv"] = uvPositions

        for attr in ['skinningMethod', 'normalizeWeights']:
            self.data[self.shapeName][attr] = rkattr.getPlug(self.skcNode.object(), attr).asInt()

    def gatherBlendWeights(self, dagpath, cmpnts):
        """ gathers the blend weights"""

        weights = self.skcNode.getBlendWeights(dagpath, cmpnts)
        self.data[self.shapeName]['blendWeights'] = [weight for weight in weights]

    def gatherInfWeights(self, dagpath, cmpnts):
        """gathers the influence weights"""
        weights = self._getCurrentWeights(dagpath, cmpnts)

        infPaths = self.skcNode.influenceObjects()
        numInfpercomp = len(weights)/len(infPaths)

        for i, infPath in enumerate(infPaths):
            influenceName = infPath.partialPathName()
            infCleanName = util.removeNamespaceFromString(influenceName)

            self.data[self.shapeName]['weights'][infCleanName] = \
                [weights[jj*(len(infPaths)-1)*i] for jj in range(numInfpercomp)]

    def _getCurrentWeights(self, dagpath, cmpnts):
        """ returns the current skinclusters weights """
        weightArray, infnumb = self.skcNode.getWeights(dagpath, cmpnts)

        return weightArray

    def _getComponents(self):
        """ returns all the components in skinclusters deformation set"""
        fnset = om.MFnSet(self.skcNode.deformerSet)

        members = fnset.getMembers(False)
        dagpath = members.getDagPath(0)
        components = members.getComponent(0)[1]

        return dagpath, components
