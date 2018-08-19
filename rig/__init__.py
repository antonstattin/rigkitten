
import os
import json
import importlib

import maya.cmds as cmds

import component
reload(component)

class Rig(object):

    def __init__(self, name="Munchkin", path=None):

        self._tasks = []
        self._name = name
        self._path = None
        self._metaNode = None

    def createMetaNode(self):

        meta = "{name}_META".format(name=self._name)

        if not cmds.objExists(meta):
            meta = cmds.createNode("network", n=meta)
            cmds.addAttr(meta, ln="rigData", dt="string")

            cmds.setAttr("{}.rigData".format(meta),
                         "[]", type="string")

        self._metaNode = meta

    def loadMetaNode(self):
        meta = cmds.ls("*_META")

        if not meta: raise RuntimeError("No meta in scene...")
        self._metaNode = meta[0]


    def loadMetaData(self):
        try:
            rigdata = eval(cmds.getAttr("{}.rigData".format(self._metaNode)))
        except:
            rigdata = cmds.getAttr("{}.rigData".format(self._metaNode))

        self._loadTasksFromDict(rigdata)

    def storeMetaData(self):
        cmds.setAttr("{}.rigData".format(self._metaNode),
                     self._serializeTasks(), type="string")

    def addComponent(self, cmpt, index=0):
        if cmpt in self._tasks:
            self._tasks.pop(self._tasks.index(cmpt))
        self._tasks.insert(index, cmpt)

    def _serializeTasks(self):
        return [task.serialize() for task in self._tasks]

    def _loadTasksFromDict(self, dData):
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

        with open("{}/{}.json".format(self._path, self._name)) as outfile:
            dTasks = json.load(outfile)

        self._loadTasksFromDict(dTasks["rig"])

    def importComponentData(self, task, stage):
        cPath = "{}/components/{}/{}".format(self._path, task.id, stage)
        if not os.path.isdir(cPath): return

        for folder in os.path.listdir(cPath):
            print folder

    def exportComponentData(self, task, stage):
        data = task.stored


    def resetComponent(self, task, method=component.kStage.GUIDE,
                       stage=component.kBuildType.PRE):

        task.stage = ".".join([method, stage])

    def _resetAllComponents(self, method=component.kStage.GUIDE,
                            stage=component.kBuildType.PRE):

        for task in self._tasks: self.resetComponent(task)

    def _importAllComponentData(self, stage):
        for task in self._tasks: self.importComponentData(task, stage)


    def guide(self):

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
