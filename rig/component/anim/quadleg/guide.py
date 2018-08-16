import maya.cmds as cmds

def pre(task): return


def run(task):

    loc = cmds.spaceLocator(n=task.name)
    task.store(task.kStoreTypes.TRANSFROM, loc)


def post(task): return
