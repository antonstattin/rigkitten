import maya.api.OpenMaya as om
from . import rkattribute, rkdecorators
reload(rkattribute)
reload(rkdecorators)

def getMMatrixFromAttr(mObj, attrStr):
    """ util script to grab matrix from attribute

        :param mObj: MObject with matrix attribute
        :type mObj: MObject

        :param attrStr: name of attribute
        :param attrStr: str

        :return: MMatrix
    """
    mfnDn = om.MFnDependencyNode(mObj)
    matrixattr =  mfnDn.attribute(attrStr)

    matrixPlug = om.MPlug( mObj, matrixattr )
    matrixPlug = matrixPlug.elementByLogicalIndex( 0 )
    matrixMObj = matrixPlug.asMObject()

    mfMatrixData = om.MFnMatrixData(matrixMObj)

    return mfMatrixData.matrix()

@rkdecorators.enable_om_undo
def spaceSwitch(*args, **kwargs):
    """
        creates a spaceSwitch from given objects

        :Arguments: first driver objects, last driven object
        :Keyword Arguments:
            * name | n  - name of setup (str)
            * maintainOffset | mo  - if setup should maintain offset (bool)
            * preventBenignCycle | pbc  - prevent benign cycles, grab parent instead of
                                   using inverseParentMatrix from driven.

        :returns: (list) decomposeMatrix
    """

    if len(args)< 2: raise ValueError("Needs at least two transforms")

    # list nodes
    mSel = om.MSelectionList()
    for obj in args: mSel.add(obj)

    # drivenObj
    dnMobj = mSel.getDependNode(mSel.length()-1)

    # query kwargs
    name = kwargs.get("name", kwargs.get("n", "matrixConstraint"))
    mo = kwargs.get("maintainOffset", kwargs.get("mo", False))
    pbc = kwargs.get("preventBenignCycle", kwargs.get("pbc", True))

    # create Matrix node(s)
    dgMod = om.MDGModifier()

    choiceMObj = dgMod.createNode("choice")
    dgMod.renameNode(choiceMObj, "_{0}_SWITCH".format(name))

    decomp = dgMod.createNode("decomposeMatrix")
    dgMod.renameNode(decomp, "_{0}_DMtx".format(name))

    if pbc:
        parentMObj = om.MFnDagNode(dnMobj).parent(0)
        parent = om.MFnDependencyNode(parentMObj)

        # if we no parent skip step else get parent and connect worldmtx
        if parent.name() != "world":
            invParMult = dgMod.createNode("multMatrix")
            dgMod.renameNode(invParMult, "_{0}_invParMtx".format(name))

            dgMod.connect(rkattribute.getPlug(choiceMObj, "output"),
                          rkattribute.getPlug(invParMult, "matrixIn").elementByLogicalIndex(0))

            dgMod.connect(rkattribute.getPlug(parentMObj, "worldInverseMatrix").elementByLogicalIndex(0),
                          rkattribute.getPlug(invParMult, "matrixIn").elementByLogicalIndex(1))

            dgMod.connect(rkattribute.getPlug(invParMult, "matrixSum"),
                          rkattribute.getPlug(decomp, "inputMatrix"))
        else:
            dgMod.connect(rkattribute.getPlug(choiceMObj, "output"),
                          rkattribute.getPlug(decomp, "inputMatrix"))

    else:
        # create bengin cycle connect driven ParentInverseMatrix
        dgMod.connect(rkattribute.getPlug(choiceMObj, "output"),
                      rkattribute.getPlug(invParMult, "matrixIn").elementByLogicalIndex(0))

        dgMod.connect(rkattribute.getPlug(dnMobj, "parentInverseMatrix"),
                      rkattribute.getPlug(invParMult, "matrixIn").elementByLogicalIndex(1))

        dgMod.connect(rkattribute.getPlug(invParMult, "matrixSum"),
                      rkattribute.getPlug(decomp, "inputMatrix"))

    for i in range(mSel.length()-1):

        drMobj = mSel.getDependNode(i)
        choiceInput = rkattribute.getPlug(choiceMObj, "input").elementByLogicalIndex(i)

        if mo:
            node_name = mSel.getDagPath(i).partialPathName().title()
            mult = dgMod.createNode("multMatrix")
            dgMod.renameNode(mult, "_{0}{1}_MO".format(name, node_name))

            inA = rkattribute.getPlug(mult, "matrixIn").elementByLogicalIndex(0)
            inB = rkattribute.getPlug(mult, "matrixIn").elementByLogicalIndex(1)
            dWs = rkattribute.getPlug(drMobj, "worldMatrix").elementByLogicalIndex(0)

            dMtx = getMMatrixFromAttr(dnMobj, "worldMatrix")
            dInvMtx = getMMatrixFromAttr(drMobj, "worldInverseMatrix")

            mtxPrdct = om.MFnMatrixData().create(dMtx * dInvMtx)
            inA.setMObject(mtxPrdct)
            dgMod.connect(dWs, inB)

            dgMod.connect(rkattribute.getPlug(mult, "matrixSum"), choiceInput)
        else:
            dgMod.connect(rkattribute.getPlug(drMobj, "worldMatrix").elementByLogicalIndex(0),
                          choiceInput)

    dgMod.connect(rkattribute.getPlug(decomp, "outputRotate"),
                  rkattribute.getPlug(dnMobj, "rotate"))

    dgMod.connect(rkattribute.getPlug(decomp, "outputTranslate"),
                  rkattribute.getPlug(dnMobj, "translate"))

    dgMod.doIt()

    return dgMod

@rkdecorators.enable_om_undo
def aimConstraint(driver, driven, **kwargs):
    """
        Creates a matrix aim constraint between two objects.
        :Keyword Arguments:
            * name | n  - name of setup (str)
            * maintainOffset | mo  - if setup should maintain offset (bool)
            # upVector | up - up vector (default Y)
            # upObject | uobj - up Object
            # aimVector | aim - aim vector (default X)
            * preventBenignCycle | pbc  - prevent benign cycles, grab parent instead of
                                   using inverseParentMatrix from driven.

        :returns: a list of strings.
    """

    mSel = om.MSelectionList()
    mSel.add(driven)
    mSel.add(driver)

    driven = mSel.getDependNode(0)
    driver = mSel.getDependNode(1)

    # query kwargs
    name = kwargs.get("name", kwargs.get("n", "matrixConstraint"))
    mo = kwargs.get("maintainOffset", kwargs.get("mo", False))
    aimVector = kwargs.get("aimVector", kwargs.get("aim", "x"))
    pbc = kwargs.get("preventBenignCycle", kwargs.get("pbc", True))


    # create modifier
    dgMod = om.MDGModifier()

    # create nodes
    fromPoint = dgMod.createNode("pointMatrixMult")
    dgMod.renameNode(fromPoint, "_{0}_fromPnt".format(name))

    toPoint = dgMod.createNode("pointMatrixMult")
    dgMod.renameNode(toPoint, "_{0}_toPnt".format(name))

    fbfm = dgMod.createNode("fourByFourMatrix")
    dgMod.renameNode(fbfm, "_{0}_fbfMtx".format(name))

    getAimVecPMA = dgMod.createNode("plusMinusAverage")
    dgMod.renameNode(getAimVecPMA, "_{0}_getAimVector".format(name))

    crossPrdct = dgMod.createNode("vectorProduct")
    dgMod.renameNode(crossPrdct, "_{0}_CrossPrdct".format(name))

    rkattribute.getPlug(crossPrdct, "operation").setInt(2)
    rkattribute.getPlug(getAimVecPMA, "operation").setInt(2)

    # connect pointMatrixMult

    dgMod.connect(rkattribute.getPlug(driver, "worldMatrix").elementByLogicalIndex(0),
                  rkattribute.getPlug(toPoint, "inMatrix"))

    dgMod.connect(rkattribute.getPlug(driver, "rotatePivot"),
                  rkattribute.getPlug(toPoint, "inPoint"))

    dgMod.connect(rkattribute.getPlug(driven, "worldMatrix").elementByLogicalIndex(0),
                  rkattribute.getPlug(fromPoint, "inMatrix"))

    dgMod.connect(rkattribute.getPlug(driven, "rotatePivot"),
                  rkattribute.getPlug(fromPoint, "inPoint"))

    if "-" in aimVector:
        dgMod.connect(rkattribute.getPlug(fromPoint, "output"),
                      rkattribute.getPlug(getAimVecPMA, "input3D").elementByLogicalIndex(1))

        dgMod.connect(rkattribute.getPlug(toPoint, "output"),
                      rkattribute.getPlug(getAimVecPMA, "input3D").elementByLogicalIndex(0))
    else:
        dgMod.connect(rkattribute.getPlug(fromPoint, "output"),
                      rkattribute.getPlug(getAimVecPMA, "input3D").elementByLogicalIndex(0))

        dgMod.connect(rkattribute.getPlug(toPoint, "output"),
                      rkattribute.getPlug(getAimVecPMA, "input3D").elementByLogicalIndex(1))



    dgMod.doIt()

    return dgMod

@rkdecorators.enable_om_undo
def constraint(*args, **kwargs):
    """
        Create a matrix constriant.  If we pass more objects this func will
        create a weighted setup.

        :Arguments: first driver objects, last driven object
        :Keyword Arguments:
            * name | n  - name of setup (str)
            * maintainOffset | mo  - if setup should maintain offset (bool)
            * preventBenignCycle | pbc  - prevent benign cycles, grab parent instead of
                                   using inverseParentMatrix from driven.

        :returns: a list of strings.
                  the name of the decomposeMatrix node and the weighted matrix node
                  if the constraint isn't weighted the function will return
                  the decompose matrix node and None.
    """

    if len(args)< 2: raise ValueError("Needs at least two transforms")

    # list nodes
    mSel = om.MSelectionList()
    for obj in args: mSel.add(obj)

    # query kwargs
    name = kwargs.get("name", kwargs.get("n", "matrixConstraint"))
    mo = kwargs.get("maintainOffset", kwargs.get("mo", False))
    pbc = kwargs.get("preventBenignCycle", kwargs.get("pbc", True))

    # create Matrix node(s)
    dgMod = om.MDGModifier()

    invParMult = dgMod.createNode("multMatrix")
    dgMod.renameNode(invParMult, "_{0}_invParMtx".format(name))

    # use this if we are parented to world
    noInverse = False

    decomposeMat = dgMod.createNode("decomposeMatrix")
    dgMod.renameNode(decomposeMat, "_{0}_DMtx".format(name))


    # drivenObj
    dnMobj = mSel.getDependNode(mSel.length()-1)

    if pbc:
        parentMObj = om.MFnDagNode(dnMobj).parent(0)
        parent = om.MFnDependencyNode(parentMObj)

        if parent.name() != "world":
            dgMod.connect(rkattribute.getPlug(parentMObj, "worldInverseMatrix").elementByLogicalIndex(0),
                          rkattribute.getPlug(invParMult, "matrixIn").elementByLogicalIndex(1))
        else: noInverse=True

    else:
        dgMod.connect(rkattribute.getPlug(dnMobj, "parentInverseMatrix"),
                      rkattribute.getPlug(invParMult, "matrixIn").elementByLogicalIndex(1))

    if not noInverse:
        dgMod.connect(rkattribute.getPlug(invParMult, "matrixSum"),
                      rkattribute.getPlug(decomposeMat, "inputMatrix"))


    if mo:
        mo_mult_mobjs = []
        for i in range(mSel.length()-1):
            node_name = mSel.getDagPath(i).partialPathName().title()
            mult = dgMod.createNode("multMatrix")
            dgMod.renameNode(mult, "_{0}{1}_MO".format(name, node_name))

            drMobj = mSel.getDependNode(i)

            inA = rkattribute.getPlug(mult, "matrixIn").elementByLogicalIndex(0)
            inB = rkattribute.getPlug(mult, "matrixIn").elementByLogicalIndex(1)
            dWs = rkattribute.getPlug(drMobj, "worldMatrix").elementByLogicalIndex(0)

            dMtx = getMMatrixFromAttr(dnMobj, "worldMatrix")
            dInvMtx = getMMatrixFromAttr(drMobj, "worldInverseMatrix")

            mtxPrdct = om.MFnMatrixData().create(dMtx * dInvMtx)
            inA.setMObject(mtxPrdct)
            dgMod.connect(dWs, inB)

            mo_mult_mobjs.append(mult)


    # if we have multiple drivers, weight them
    if mSel.length() > 2:
        wtMat = dgMod.createNode("wtAddMatrix")
        dgMod.renameNode(wtMat, "_{0}_WtMtx".format(name))

        wt = 1.0/(mSel.length()-1)

        if mo:
            for i, mult in enumerate(mo_mult_mobjs):
                wtMatrixCmpnd = rkattribute.getPlug(wtMat, "wtMatrix").elementByLogicalIndex(i)
                mtrxIn = wtMatrixCmpnd.child(0)
                wtMatrixCmpnd.child(1).setFloat(wt)
                dgMod.connect(rkattribute.getPlug(mult, "matrixSum"), mtrxIn)
        else:
            for i in range(mSel.length()-1):
                mobj = mSel.getDependNode(i)
                wtMatrixCmpnd = rkattribute.getPlug(wtMat, "wtMatrix").elementByLogicalIndex(i)
                mtrxIn = wtMatrixCmpnd.child(0)
                wtMatrixCmpnd.child(1).setFloat(wt)

                dgMod.connect(rkattribute.getPlug(mobj, "worldMatrix").elementByLogicalIndex(0), mtrxIn)


        if noInverse:
            dgMod.connect(rkattribute.getPlug(wtMat, "matrixSum"),
                          rkattribute.getPlug(decomposeMat, "inputMatrix"))
        else:
            dgMod.connect(rkattribute.getPlug(wtMat, "matrixSum"),
                      rkattribute.getPlug(invParMult, "matrixIn").elementByLogicalIndex(0))

    else:
        if noInverse:
            if mo:
                drvNode = mo_mult_mobjs[0]
                dgMod.connect(rkattribute.getPlug(drvNode, "matrixSum"),
                              rkattribute.getPlug(decomposeMat, "inputMatrix"))
            else:

                dgMod.connect(rkattribute.getPlug(mSel.getDependNode(0),
                              "worldMatrix").elementByLogicalIndex(0),
                              rkattribute.getPlug(decomposeMat, "inputMatrix"))
        else:
            if mo:
                drvNode = mo_mult_mobjs[0]
                dgMod.connect(rkattribute.getPlug(drvNode, "matrixSum"),
                             rkattribute.getPlug(invParMult, "matrixIn").elementByLogicalIndex(0))
            else:
                dgMod.connect(rkattribute.getPlug(mSel.getDependNode(0),
                              "worldMatrix").elementByLogicalIndex(0),
                              rkattribute.getPlug(invParMult, "matrixIn").elementByLogicalIndex(0))

    dgMod.connect(rkattribute.getPlug(decomposeMat, "outputRotate"),
                  rkattribute.getPlug(dnMobj, "rotate"))

    dgMod.connect(rkattribute.getPlug(decomposeMat, "outputTranslate"),
                  rkattribute.getPlug(dnMobj, "translate"))

    dgMod.doIt()

    if noInverse:
        dgMod.deleteNode(invParMult)

    # return weightMatrix node if we created one..
    if mSel.length() > 2:
        return dgMod, om.MFnDependencyNode(decomposeMat).name(), om.MFnDependencyNode(wtMat).name()
    else: return dgMod, om.MFnDependencyNode(decomposeMat).name()
