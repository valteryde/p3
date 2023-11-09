
tree = {}
import logging

escape = False
def selectWrapper(func, parentfunc=None, *args, **kwargs):
    global escape

    try:
        if escape:
            return
        
        if not func:
            return

        if parentfunc:
            tree[func] = parentfunc

        funcres = func()
        if funcres:
            escape = True

        if not escape and parentfunc:
            selectWrapper(tree[func])
    except KeyboardInterrupt:
        escape = True