
import os
import json
import rigkitten.rig.component as cmpnt

class Rig(object):

    def __init__(self, name="Munchkin", path=None):

        self._tasks = []
        self._name = name
        self._path = None

    def addComponent(self, cmpt, index=0):
        if cmpt in self._tasks:
            self._tasks.pop(self._tasks.index(cmpt))
        self._tasks.insert(index, cmpt)

    def _serializeTasks(self):
        return [task.serialize() for task in self._tasks]

    def save(self):
        """ save rig to json """
        if not os.path.isdir(self._path): return

        dTasks = self._serializeTasks()
        with open("{}/{}.json".format(self._path, self._name), 'w') as outfile:
            json.dump(dTasks, outfile, indent=4)

    def load(self): return

    def importComponentData(self, task, stage):
        cPath = "{}/components/{}/{}".format(self.path, task.id, stage)
        if not os.path.isdir(cPath): return

    def _importAllComponentData(self, stage):
        for task in self._tasks:
            self.importComponentData(task, stage)

    def guide(self):

        # run pre
        for task in self._tasks:
            if task.stage == "init":
                task.guide(bType=cmpnt.kBuildType.PRE)

        self._importAllComponentData(".".join(["guide",cmpnt.kBuildType.PRE]))

        # run build
        for task in self._tasks:
            if task.stage == ".".join(["guide",cmpnt.kBuildType.PRE]):
                task.guide(bType=cmpnt.kBuildType.RUN)

        self._importAllComponentData(".".join(["guide",cmpnt.kBuildType.RUN]))

        # run post
        for task in self._tasks:
            if task.stage == ".".join(["guide",cmpnt.kBuildType.RUN]):
                task.guide(bType=cmpnt.kBuildType.POST)

        self._importAllComponentData(".".join(["guide",cmpnt.kBuildType.POST]))


    def build(self):

        # run pre
        for task in self._tasks:
            if task.stage == ".".join(["guide",cmpnt.kBuildType.POST]):
                task.build(bType=cmpnt.kBuildType.PRE)

        self._importAllComponentData(".".join(["build",cmpnt.kBuildType.PRE]))

        # run build
        for task in self._tasks:
            if task.stage == ".".join(["build",cmpnt.kBuildType.PRE]):
                task.build(bType=cmpnt.kBuildType.RUN)

        self._importAllComponentData(".".join(["build",cmpnt.kBuildType.RUN]))

        # run post
        for task in self._tasks:
            if task.stage == ".".join(["build",cmpnt.kBuildType.RUN]):
                task.build(bType=cmpnt.kBuildType.POST)

        self._importAllComponentData(".".join(["build",cmpnt.kBuildType.POST]))

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
