
from ... import component
reload(component)

class kSideSuffix(object):
    CENTER = 0
    LEFT = 1
    RIGHT = 2

class AnimComponent(component.BaseComponent):
    def __init__(self, *arg, **kwargs):
        super(AnimComponent, self).__init__(*arg, **kwargs)
