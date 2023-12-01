
try:
    import pyglet as pg
except ImportError:
    print('Gui is not avaliable')
from multiprocessing import Process
import os, sys
from .parser import getSortedFolder, loadASCII, convertFramesToImages
from PIL import Image
import numpy as np

AMP = 6
image = None
def __update__(dt, folder, ASCII):
    global image
    try:
        if not ASCII:
            file = getSortedFolder(os.path.join(folder,'*.png'))[-2]
        else:
            file = getSortedFolder(os.path.join(folder,'*.asc'))[-2]

        if ASCII:
            data = loadASCII(file)
            convertFramesToImages([data["map"]], [".__gui.png"], strictNames=True, relativeTempScale=False)
            img = pg.image.load('.__gui.png')
            os.remove('.__gui.png')
        else:
            img = pg.image.load(file)
        image = pg.sprite.Sprite(img=img,x=0,y=0)
        width, height = image.width*AMP, image.height*AMP
        image.width = width
        image.height = height
    except Exception as e:
        type, value, traceback = sys.exc_info()
        if type == IndexError:
            return
        print('[UPDATE:ERROR]', e, type, value, traceback)


def __live__(size, folder, ASCII):
    window = pg.window.Window(size[0]*AMP, size[1]*AMP)

    @window.event
    def on_draw():
        window.clear()
        try:
            if image: image.draw()
        except Exception as e: 
            print('[DRAW:ERROR]',e)

    pg.clock.schedule_interval(__update__, 1/60, folder, ASCII)
    pg.app.run()


process = None
def liveViewer(size, folder, ASCII):
    global process
    size = size[1],size[0]
    p = Process(target=__live__, args=(size,folder,ASCII))
    p.start()
    process = p
    return p


def closeLiveViewer():
    process.join()
    process.close()


