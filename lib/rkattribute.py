import maya.api.OpenMaya as om

def connect(srcMObj, srcAttr, destMObj, dstAttr, mDgModifier):
    """ A util script for creating connections and preventing code repitation..

        :param srcMObj: source object (connected from)
        :type srcMObj: MObject

        :param srcAttr: source attribute name
        :type srcAttr: str

        :param destMObj: dst object (connect to)
        :type destMObj: MObject

        :param dstAttr: name of dst attribute
        :type dstAttr: str

        :param mDgModifier: mdfmodifier object
        :type mDgModifier: MDGModifier

    """

    srcMfnDN = om.MFnDependencyNode(srcMObj)
    destMfnDN = om.MFnDependencyNode(destMObj)

    srcPlug = srcMfnDN.attribute(srcAttr)
    dstPlug = destMfnDN.attribute(dstAttr)

    mDgModifier.connect(srcMObj, srcPlug, destMObj, dstPlug)
