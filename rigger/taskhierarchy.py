import uuid

class TaskObj(object)
    def __init__(self):

        self._name = 'null'
        self._id = str(uuid.uuid4()).split("-")[0]
        self._taskHierarchy = None

class TaskLayer(TaskObj):
    def __init__(self):

        self._tasks = []
        self._params = []

class Task(TaskObj):

    def __init__(self):
        self._params = []

class Param(TaskObj):
    def __init__(self):

        # parameters value
        self._value = ''

        # info about the param
        self._info = ''

        # value expresison
        self._expr = ''

        # value func
        self._fnc = None

    @property
    def value(self): return self._value

    @value.setter
    def value(self, val):
        self._value = val

    def _evalExpr(self):
        """ updates value from expression """
        if self._expr == '': return self._value

        # string to parse
        rawExpression = self._expr

        # look for task-expressions
        toConvert = re.findall("(@\w+.\w+)", rawExpression)

        if toConvert:
            for exprVar in toConvert:
                name = toConvert.split(".")[0].replace("@", "")
                var =  toConvert.split(".")[1]

                # find by name
                task = self._taskHierarchy.findByName(name)
                if not task: task = self._taskHierarchy.findById(name)

                # if task have the variable, find the value
                if task:
                    if hasattr(task, var): rawExpression.replace(exprVar,
                                           str(getattr(task, var)))

        # use eval to build the final expression
        try: return eval(rawExpression)
        except: return rawExpression

class ParamGroup(TaskObj):
    def __init__(self):
        self._params = []

class TaskHierarchy(object):
    def __init__(self):

        self._layers = []
        self._params = []

    def findById(self, taskobj):
        raise NotImplementedError()

    def findByName(self, taskobj):
        raise NotImplementedError()
