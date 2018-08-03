import maya.api.OpenMaya as om

def set(inPlug, inValue):

    #plugAttribute = inPlug.attribute()
    apiType = inPlug.apiType()

    print apiType

    # Float Groups - rotate, translate, scale
    if apiType in [ om.MFn.kAttribute3Double, om.MFn.kAttribute3Float ]:

        result = []
        if inPlug.isCompound():

            if isinstance( inValue, list ):

                for c in xrange( inPlug.numChildren() ):

                    result.append( setPlugValue( inPlug.child( c ), inValue[ c ] ) )

                return result

            elif type( inValue ) == om.MEulerRotation:

                setPlugValue( inPlug.child( 0 ), inValue.x )
                setPlugValue( inPlug.child( 1 ), inValue.y )
                setPlugValue( inPlug.child( 2 ), inValue.z )

            else:

                raise ValueError( '{0} :: Passed in value ( {1} ) is {2}. Needs to be type list.'.format( inPlug.info(), inValue, type( inValue ) ) )

    # Distance
    elif apiType in [ om.MFn.kDoubleLinearAttribute, om.MFn.kFloatLinearAttribute ]:

        if isinstance( inValue, float ):

            value =  om.MDistance( inValue, om.MDistance.kCentimeters )
            inPlug.setMDistance( value )

        else:
            raise ValueError( '{0} :: Passed in value ( {1} ) is {2}. Needs to be type float.'.format( inPlug.info(), inValue, type( inValue ) ) )

    # Angle
    elif apiType in [ om.MFn.kDoubleAngleAttribute, om.MFn.kFloatAngleAttribute ]:

        if isinstance( inValue, float ):

            value = om.MAngle( inValue, om.MAngle.kDegrees )
            inPlug.setMAngle( value )
        else:
            raise ValueError( '{0} :: Passed in value ( {1} ) is {2}. Needs to be type float.'.format( inPlug.info(), inValue, type( inValue ) ) )

    # MATRIX

    elif apiType == om.MFn.kMatrixAttribute:

        if isinstance( inValue, om.MPlug ):

            # inValue must be a MPlug!
            sourceValueAsMObject = om.MFnMatrixData( inValue.asMObject() ).object()
            inPlug.setMObject( sourceValueAsMObject )
        else:
            raise ValueError( 'Value object is not an MPlug. To set a MMatrix value, both passed in variables must be MPlugs.' )


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
