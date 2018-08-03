import maya.api.OpenMaya as om
from . import rkattribute, rkdecorators
reload(rkattribute)
reload(rkdecorators)

def getMMatrix(mObj, attrStr):
    """ util script to grab matrix from attribute

        :param mObj: MObject with matrix attribute
        :type mObj: MObject

        :param attrStr: name of attribute
        :param attrStr: str
    """
    mfnDn = om.MFnDependencyNode(mObj)
    matrixattr =  mfnDn.attribute(attrStr)

    matrixPlug = om.MPlug( mObj, matrixattr )
    matrixPlug = matrixPlug.elementByLogicalIndex( 0 )
    matrixMObj = matrixPlug.asMObject()

    mfMatrixData = om.MFnMatrixData(matrixMObj)

    print mfMatrixData.matrix()

    return mfMatrixData.matrix()



@rkdecorators.enable_om_undo
def constraint(*args, **kwargs):
    """
        Create a matrix constriant.  If we pass more objects this func will
        create a weighted setup.

        :Arguments: first driver objects, last driven object
        :Keyword Arguments:
            * name | n  - name of setup (str)
            * maintainOffset | mo  - if setup should maintain offset (bool)
            * preventBenign | b  - prevent benign cycles, grab parent instead of
                                   using inverseParentMatrix from driven.

        :returns: a list of strings.
                  the name of the decomposeMatrix node and the weighted matrix node
                  if the constraint isn't weighted the function will return
                  the decompose matrix node and None.
    """
    # checks
    if len(args)< 2: raise ValueError("Needs at least two transforms")

    # list nodes
    mSel = om.MSelectionList()
    for obj in args: mSel.add(obj)

    # query kwargs
    name = kwargs.get("name", kwargs.get("n", "matrixConstraint"))
    mo = kwargs.get("maintainOffset", kwargs.get("mo", False))
    pb = kwargs.get("preventBenign", kwargs.get("b", True))

    # create Matrix node(s)
    dgMod = om.MDGModifier()
    invParMult = dgMod.createNode("multMatrix")
    dgMod.renameNode(invParMult, "_{0}_InverseParent".format(name))

    decomposeMat = dgMod.createNode("decomposeMatrix")
    dgMod.renameNode(decomposeMat, "_{0}_DMAT".format(name))

    rkattribute.connect(invParMult, "matrixSum", decomposeMat, "inputMatrix", dgMod)

    # if we have multiple drivers, weight them
    if mSel.length() > 2:
        wtMat = dgMod.createNode("wtAddMatrix")
        dgMod.renameNode(wtMat, "_{0}_weightMatrix".format(name))

        if mo:
            mo_mobjs = []
            for i in range(mSel.length()-1):
                node_name = mSel.getDagPath(i).partialPathName().title()
                mm = dgMod.createNode("multMatrix")
                dgMod.renameNode(mm, "_{0}{1}_MO".format(name, node_name))
                mo_mobjs.append(mm)
    else:
        if mo:
            MObjDriver = mSel.getDependNode(0)
            MObjDriven = mSel.getDependNode(1)

            node_name = mSel.getDagPath(0).partialPathName().title()
            mm = dgMod.createNode("multMatrix")
            dgMod.renameNode(mm, "_{0}{1}_MO".format(name, node_name))

            drivInvMat = getMMatrix(MObjDriver, "worldMatrix")
            drivMat = getMMatrix(MObjDriver, "worldMatrix")

            print mm.apiType()

            

            #print inPlug.name()

            #print inPlug.isCompound

            #rkattribute.set(inPlug, drivMat * drivInvMat)
            #rkattribute.connect(MObjDriven, "worldMatrix", mm, "matrixIn[1]", dgMod)

    dgMod.doIt()

    mmDn= om.MFnDependencyNode(mm)

    inPlug = mmDn.findPlug("matrixIn", False)

    print inPlug.name()


    return dgMod, om.MFnDependencyNode(decomposeMat).name()
