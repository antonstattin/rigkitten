
import os
import re
import json
import importlib
from . import cio
reload(cio)

import maya.cmds as cmds

import component
reload(component)

class Rig(object):

    def __init__(self, name="Munchkin", path=None):

        self._tasks = []
        self._name = name
        self._path = ""
        self._metaNode = None

    @property
    def path(self): return self._path

    @path.setter
    def path(self, value):
        self._path = value

        # set project path
        if self._metaNode:
            if not cmds.attributeQuery('projectPath', node=self._metaNode, exists=True):
                cmds.addAttr(meta, ln="projectPath", dt="string")
            cmds.setAttr("{}.projectPath".format(meta), value, type="string")

    def createMetaNode(self):
        """ creates projects meta node """

        meta = "{name}_META".format(name=self._name)

        if not cmds.objExists(meta):
            meta = cmds.createNode("network", n=meta)
            cmds.addAttr(meta, ln="rigData", dt="string")

            cmds.setAttr("{}.rigData".format(meta),
                         "[]", type="string")

        self._metaNode = meta

    def loadMetaNode(self):
        """ loads meta node """
        meta = cmds.ls("*_META")

        if not meta: raise RuntimeError("No meta in scene...")
        self._metaNode = meta[0]

    def loadMetaData(self):
        """ loads meta data from meta node """
        try:
            rigdata = eval(cmds.getAttr("{}.rigData".format(self._metaNode)))
        except:
            rigdata = cmds.getAttr("{}.rigData".format(self._metaNode))

        # set component data
        self._loadTasksFromDict(rigdata)

        # set project path
        if cmds.attributeQuery('projectPath', node=self._metaNode, exists=True):
            self._path = cmds.getAttr("{}.projectPath".format(self._metaNode))

    def storeMetaData(self):
        """ serialize and save the data in this class to the metanode """
        cmds.setAttr("{}.rigData".format(self._metaNode),
                     self._serializeTasks(), type="string")

    def addComponent(self, cmpt, index=0):
        """ add a new component to rig

            :param cmpt: the component
            :type cmpt: component

            :param index: where in the buildorder this component should be built
            :type index: int
        """
        if cmpt in self._tasks:
            self._tasks.pop(self._tasks.index(cmpt))
        self._tasks.insert(index, cmpt)

    def _serializeTasks(self):
        """ serialize all tasks """
        return [task.serialize() for task in self._tasks]

    def _loadTasksFromDict(self, dData):
        """ load data from dictonary """
        self._tasks = []
        for dTask in dData:

            modpath = dTask["module"]

            taskmod = importlib.import_module(modpath)

            fTasks = {}
            for key, data in dTask.items():
                if isinstance(data, int): fTasks.update({key:{"value":data}})
                elif isinstance(data, unicode): fTasks.update({key:{"value":data}})
                elif isinstance(data, bool): fTasks.update({key:{"value":data}})
                elif isinstance(data, dict): fTasks.update({key:{"value":data}})
                elif isinstance(data, list): fTasks.update({key:{"value":data}})
                else: fTasks.update({key:{"value":str(data)}})

            task = taskmod.Task(**fTasks)
            self._tasks.append(task)

    def save(self):
        """ save rig to json """
        if not os.path.isdir(self._path): return

        dTasks = {"rig":self._serializeTasks()}
        with open("{}/{}.json".format(self._path, self._name), 'w') as outfile:
            json.dump(dTasks, outfile, indent=4)

    def load(self):
        """ load rig data from a json file"""
        with open("{}/{}.json".format(self._path, self._name)) as outfile:
            dTasks = json.load(outfile)

        self._loadTasksFromDict(dTasks["rig"])

    def importComponentData(self, taskId, stage, dtype):
        """ import component data like transform or deformer weights

            :param id: id of component
            :type id: str

            :param stage: import stage
            :type stage: str

            :param dtype: type of data
            :type stage: str
        """
        cPath = "{}/.taskdata/{}/{}/{}".format(self._path, taskId, stage, dtype)
        if not os.path.isdir(cPath): return

        highestVersion = 0
        latestDFile = None
        for dFile in os.listdir(cPath):
            version = int(re.search('\d\d\d', dFile).group(0))
            if version > highestVersion:
                highestVersion = version
                latestDFile = "{}/{}".format(cPath, dFile)

        iocls = getattr(cio, dtype)
        iocls.importData(latestDFile)

    def exportComponentData(self, task, stage, dtype="all"):
        """ export component data

            :param task: component to grab data from
            :type task: component

            :param stage: stage to export to
            :type stage: str

            :param dtype: type of data to export
            :type dtype: str
        """

        if not os.path.isdir(self._path):
            raise OSError("The folder '{}' doesn't exist".format(self._path))

        if not os.path.isdir(self._path + "/.taskdata"):
            os.mkdir(self._path + "/.taskdata")

        if not os.path.isdir("{}/.taskdata/{}".format(self._path, task.id)):
            os.mkdir("{}/.taskdata/{}".format(self._path, task.id))

        exportpath = "{}/.taskdata/{}/{}".format(self._path, task.id, stage)
        if not os.path.isdir(exportpath): os.mkdir(exportpath)

        data = task.stored
        for key in data[stage].keys():
            if dtype == "all" or key == dtype:

                if not os.path.isdir("{}/{}".format(exportpath, key)):
                    os.mkdir("{}/{}".format(exportpath, key))

                iocls = getattr(cio, key)
                iocls.exportData("{}/{}".format(exportpath, key), data[stage][key])


    def resetComponent(self, task, method=component.kStage.GUIDE,
                       stage=component.kBuildType.PRE):

        task.stage = ".".join([method, stage])

    def _resetAllComponents(self, method=component.kStage.GUIDE,
                            stage=component.kBuildType.PRE):

        for task in self._tasks: self.resetComponent(task)

    def _importAllComponentData(self, stage):

        # deal with order of data import
        transformIOList = []
        hierarchyIOList = []
        allIOList = []

        for task in self._tasks:
            if not stage in task.stored.keys(): continue

            for key in task.stored[stage].keys():
                if key == "TransformIO": transformIOList.append(task)
                elif key == "HierarchyIO": hierarchyIOList.append(task)
                else: allIOList.append(task)

        # import in order
        for task in transformIOList:
            self.importComponentData(task.id, stage, "TransformIO")

        for task in hierarchyIOList:
            self.importComponentData(task.id, stage, "HierarchyIO")

        for task in allIOList:
            for key in task.stored[stage].keys():
                if key == "TransformIO" or key == "HierarchyIO": continue

                self.importComponentData(task.id, stage, key)


    def guide(self):

        cmds.undoInfo(ock=True)
        # run pre
        for task in self._tasks:
            if task.stage == "init":
                task.guide(bType=component.kBuildType.PRE)

        self._importAllComponentData(".".join([component.kStage.GUIDE,
                                               component.kBuildType.PRE]))

        # run build
        for task in self._tasks:
            if task.stage == ".".join([component.kStage.GUIDE,
                                       component.kBuildType.PRE]):
                task.guide(bType=component.kBuildType.RUN)

        self._importAllComponentData(".".join([component.kStage.GUIDE,
                                               component.kBuildType.RUN]))

        # run post
        for task in self._tasks:
            if task.stage == ".".join([component.kStage.GUIDE,
                                       component.kBuildType.RUN]):
                task.guide(bType=component.kBuildType.POST)

        self._importAllComponentData(".".join([component.kStage.GUIDE,
                                               component.kBuildType.POST]))
        cmds.undoInfo(cck=True)

    def build(self):

        # run pre
        for task in self._tasks:
            if task.stage == ".".join([component.kStage.GUIDE,
                                       component.kBuildType.POST]):
                task.build(bType=component.kBuildType.PRE)

        self._importAllComponentData(".".join([component.kStage.BUILD,
                                               component.kBuildType.PRE]))

        # run build
        for task in self._tasks:
            if task.stage == ".".join([component.kStage.BUILD,
                                       component.kBuildType.PRE]):
                task.build(bType=component.kBuildType.RUN)

        self._importAllComponentData(".".join([component.kStage.BUILD,
                                               component.kBuildType.RUN]))

        # run post
        for task in self._tasks:
            if task.stage == ".".join([component.kStage.BUILD,
                                       component.kBuildType.RUN]):
                task.build(bType=component.kBuildType.POST)

        self._importAllComponentData(".".join([component.kStage.BUILD,
                                               component.kBuildType.POST]))

    def __len__(self): return len(self._tasks)

    def __iter__(self):
        for task in self._tasks: yield task

    def __getitem__(self, key):
        return self._tasks[key]

    def __str__(self):
        msg = "\n-- %s Builder (%d Tasks)--\n\n"%(self._name.title(), len(self._tasks))
        for i, task in enumerate(self._serializeTasks()):
            msg +="\tIndex(%d)\n"%(i)

            for key in task.keys():
                msg +="\t\t - {} : {}\n".format(key, task[key])

        return msg
