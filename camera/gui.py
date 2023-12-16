
import pyglet as pg
from .png import loadFile, mapColor
from PIL import Image
import time
import os


class Box:

    def __init__(self, x, y, width, height, color=(255,0,0), thickness=2):
        self.batch = pg.shapes.Batch()
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.l1 = pg.shapes.Line(x, y, x+width, y, batch=self.batch, color=color, width=thickness)
        self.l2 = pg.shapes.Line(x, y, x, y+height, batch=self.batch, color=color, width=thickness)
        self.l3 = pg.shapes.Line(x+width, y, x+width, y+height, batch=self.batch, color=color, width=thickness)
        self.l4 = pg.shapes.Line(x, y+height, x+width, y+height, batch=self.batch, color=color, width=thickness)

    def setPos(self, x, y):
        self.x = x
        self.y = y
        
        self.l1.x = x
        self.l1.y = y
        self.l1.y2 = y
        self.l2.x = x
        self.l2.y = y
        self.l2.x2 = x
        self.l3.y = y
        self.l4.x = x

        self.setSize(self.width, self.height)

    def setSize(self, width, height):
        self.l1.x2 = self.x + width
        self.l2.y2 = self.y + height
        self.l3.x = self.x + width
        self.l3.x2 = self.x + width
        self.l3.y2 = self.y + height
        self.l4.y = self.y + height
        self.l4.x2 = self.x + width
        self.l4.y2 = self.y + height
        
        self.width = width
        self.height = height


    def draw(self):
        self.batch.draw()


lastPos = None
def choiceMask(file, res, maxBoxes=4):
    data = loadFile(file)
    im = Image.fromarray(mapColor(*data))
    fname = '.__guichoice.png'
    im.save(fname)

    window = pg.window.Window(im.width, im.height)
    window.set_caption('Vælg {} områder'.format(maxBoxes))

    boxes = []
    image = pg.image.load(os.path.abspath(fname))

    previewBox = Box(0, 0, 0, 0, color=(255,255,0))

    @window.event
    def on_mouse_press(x, y, *o):
        global lastPos

        if not lastPos:
            lastPos = x, y
            previewBox.setPos(x,y)
            return
        
        previewBox.setSize(0,0)
        x0, y0 = lastPos
        boxes.append(Box(x0, y0, x-x0, y-y0))
        lastPos = None

        if len(boxes) == maxBoxes-1:
            window.set_caption('Vælg et område mere')
        elif len(boxes) == maxBoxes:
            # pg.app.event_loop.exit()
            # window.close()
            #pg.app.exit()
            res[0] = boxes
            window.set_visible(False)
        else:
            window.set_caption('Vælg {} områder mere'.format(maxBoxes-len(boxes)))


    @window.event
    def on_mouse_motion(x, y, *o):
        if lastPos:
            x0, y0 = lastPos
            previewBox.setSize(x-x0, y-y0)


    @window.event
    def on_draw():
        window.clear()
        image.blit(0, 0)
        for box in boxes:
            box.draw()
        previewBox.draw()
    
    @window.event       
    def on_close():
        res[0] = -1

    pg.app.run()

