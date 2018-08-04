import maya.api.OpenMaya as om

def getPlug(srcMObj, srcAttr):
    """ A fast way to get the plug object
        :param srcMObj: the mObject where we want to find plug
        :type srcMObj: MObject

        :param srcAttr: name of attribute
        :type srcAttr: str

        :return: MPlug
    """
    srcMfnDN = om.MFnDependencyNode(srcMObj)
    srcPlug = srcMfnDN.findPlug(srcAttr, False)

    return srcPlug
