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
    dgMod.renameNode(invParMult, "_{0}_InverseParent".format(name))

    # use this if we are parented to world
    noInverse = False

    decomposeMat = dgMod.createNode("decomposeMatrix")
    dgMod.renameNode(decomposeMat, "_{0}_DMAT".format(name))


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

            dMtx = getMMatrix(dnMobj, "worldMatrix")
            dInvMtx = getMMatrix(drMobj, "worldInverseMatrix")

            mtxPrdct = om.MFnMatrixData().create(dMtx * dInvMtx)
            inA.setMObject(mtxPrdct)
            dgMod.connect(dWs, inB)

            mo_mult_mobjs.append(mult)


    # if we have multiple drivers, weight them
    if mSel.length() > 2:
        wtMat = dgMod.createNode("wtAddMatrix")
        dgMod.renameNode(wtMat, "_{0}_weightMatrix".format(name))

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
