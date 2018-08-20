import maya.cmds as cmds
import logging
import json
import re
import os

class kStoreTypes(object):

    TRANSFROM = "TransformIO"
    HIERARCHY = "HierarchyIO"

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


def latestVersion(folderpath):

    if not len(os.listdir(folderpath)):
        return "1".zfill(3)

    highestVersion = 0
    for dFile in os.listdir(folderpath):
        version = int(re.search('\d\d\d', dFile).group(0))
        if version > highestVersion:
            highestVersion = version

    return str(highestVersion+1).zfill(3)


class TransformIO(object):

    @classmethod
    def importData(cls, **kwargs): return

    @classmethod
    def exportData(cls, exportpath, listData):

        transforms = []
        notfound = []

        # sort all objects to one big list
        for dData in listData:
            for obj in dData["objects"]:
                if cmds.objExists(obj): transforms.append(obj)
                else: notfound.append(obj)


        if notfound:
            logging.warning("can't find [{}]".format(",".join(notfound)))

        data = {}
        for transform in transforms:
            translate = cmds.xform(transform, t=True, ws=True, q=True)
            rotate = cmds.xform(transform, ro=True, ws=True, q=True)
            scale = cmds.xform(transform, scale=True, ws=True, q=True)

            data.update({removeNamespaceFromString(transform):{"t":translate,"r":rotate, "s":scale}})

        version = latestVersion(exportpath)
        with open("{}/{}{}.json".format(exportpath, "transform", version), 'w') as outfile:
            json.dump(data, outfile, indent=4)

        logging.info("Exported new Transform data. V{} to {}".format(version, exportpath))

class HierarchyIO(object):

    @classmethod
    def importData(cls, **kwargs): return

    @classmethod
    def exportData(cls, exportpath, listData): return
