
import rigkitten.rig.component as cmpt

class kSideSuffix(object):
    CENTER = 0
    LEFT = 1
    RIGHT = 2

class AnimComponent(cmpt.BaseComponent):
    def __init__(self, *arg, **kwargs):
        super(AnimComponent, self).__init__(*arg, **kwargs)
