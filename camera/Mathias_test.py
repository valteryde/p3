import os
import glob
from kaxe import plot, objects, regression
from kaxe.data import loadExcel
import numpy as np
from PIL import Image
import math
from .apply import createCalFunction, callibrateExcel
from interface import selectionWindow, displayData
from interface import selectWrapper as wrapper


def showImageMT(path):
    print('Laver graf (vent venligst)')
    xlsx = glob.glob(os.path.join(path, 'temperature', '*.xlsx'))

    data = []
    for file in xlsx:
        data.extend(loadExcel(file, 'Sheet', (1,1), (4,-1)))

    inner = [(i[1],i[2]) for i in data]
    outer = [(i[3],i[0]) for i in data]
    data = [*inner, *outer]

    pl = plot.Plot()
    pl.style(windowHeight=2000,windowWidth=2000,fontSize=60)
    pl.title(first='Blank overflade', second='Malet overflades')

    x = [i[0] for i in data]
    y = [i[1]-i[0] for i in data]
    p = objects.Points(x,y, size=15,color=(242,196,58,255)).legend('Målt')
    pl.add(p)

    #minmaxy = [y[i] for i in range(len(y))]

    #pl.add(objects.Function(lambda x, a: a, a=max(minmaxy)).legend('Max: {}'.format(round(max(minmaxy),3))))
    #pl.add(objects.Function(lambda x, a: a, a=min(minmaxy)).legend('Min: {}'.format(round(min(minmaxy),3))))

    pl.save('.__prereg.png')
    im = Image.open('.__prereg.png')
    #os.remove('.__prereg.png')
    im.show()
    im.close()


def starLineExpressMT(path):
    basepath = 'files'
    files = os.listdir(basepath)

    files = [i for i in files if i not in [".DS_Store", 'config.json'] and '.' not in i and i[-4:] not in ['-res', '-cal']]
    choice = selectionWindow('Vælg mappe',["<-- Gå tilbage", "[Klik her for at åbne mappe]"] + files)

    if choice[0] == 0: 
        return False
    
    if choice[0] == 1:
        openFilesFolder()
        return False
    
    analyzeFromFolder(os.path.join(basepath,choice[1]), 'files')
    clear()
    print('\033[96m'+'Når denne process er færdig, vil dataen blive vist på en graf. Læg her mærke til hop i HDR. Disse værdier skal bruges efterfølgende'+'\033[0m')
    showImageMT(os.path.join(basepath,choice[1]+'-res'))
    typereg = selectionWindow('Vælg type af regression',REGRESSIONSNAMES)
    resetColor()
    createRegression(os.path.join(basepath,choice[1]+'-res'), *REGRESSIONS[typereg[0]])
    return True
