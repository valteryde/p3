
import glob
import numpy as np
from PIL import Image, ImageDraw
import math
import time
import os
import tqdm
from .loader import loadASCIIFile as loadFile
from .map import heatmap

COLORCHECKPOINTS = heatmap

MINTEMP = 20
MAXTEMP = 500

def mapTempToColor(col, mn=MINTEMP, mx=MAXTEMP):

    n = (col - mn) / (mx - mn)
    n = (len(COLORCHECKPOINTS)-1) * n

    upper = min(math.ceil(n), len(COLORCHECKPOINTS)-1)
    lower = max(math.floor(n), 0)

    r = n - lower
    if r < 0:
        return [*COLORCHECKPOINTS[lower], 255]

    try:
        c = [
            round(COLORCHECKPOINTS[lower][0] + (COLORCHECKPOINTS[upper][0] - COLORCHECKPOINTS[lower][0])*r),
            round(COLORCHECKPOINTS[lower][1] + (COLORCHECKPOINTS[upper][1] - COLORCHECKPOINTS[lower][1])*r),
            round(COLORCHECKPOINTS[lower][2] + (COLORCHECKPOINTS[upper][2] - COLORCHECKPOINTS[lower][2])*r),
            255
        ]
    except IndexError:
        return [*COLORCHECKPOINTS[-1], 255]

    return c


def mapColor(data, minTemp, maxTemp):
    
    # make pixels
    for rowNum, row in enumerate(data):
        
        for colNum, col in enumerate(row):
            
            data[rowNum][colNum] = mapTempToColor(col, minTemp, maxTemp)
    
    return np.array(data, np.uint8)


def addScale(image, minTemp, maxTemp, width, height, offset):
    
    draw = ImageDraw.Draw(image)

    padding = 2
    totalSteps = height - 2*padding
    size = maxTemp - minTemp
    stepSize = size / totalSteps
    l = [[mapTempToColor(minTemp + stepSize * i, minTemp, maxTemp)]*(width-padding*2) for i in range(totalSteps)]

    l.reverse()

    colorImage = Image.fromarray(np.array(l, np.uint8))
    
    draw.rectangle((*offset, width+offset[0], height+offset[1]), fill=(255,255,255,255))

    draw.text((offset[0],offset[1]-10), str(round(maxTemp,1)), fill=(255,255,255,255))
    draw.text((offset[0],offset[1]+height), str(round(minTemp,1)), fill=(255,255,255,255))

    image.paste(colorImage, (padding+offset[0],padding+offset[1]))


def createImage(outputfolderName, fileName, num=-1, filesInResFolder=[], fileLength=0):
    now = time.time()

    filename = os.path.basename(fileName).replace('.asc', '.png')
        
    if filename in filesInResFolder:
        print('\033[93m','Skipping',os.path.split(fileName)[1], '{}/{}'.format(num,fileLength), round(100*(time.time() - now), 4), 'ms', '\033[0m')
        return

    data = loadFile(fileName)
    im = Image.fromarray(mapColor(*data))
    # addScale(im, data[1], data[2], 30, 400, (im.width - 40, im.height//2 - 200))
    fname = '{}/{}'.format(outputfolderName,filename)
    im.save(fname)
    return fname


def saveAllImages(folderName,prefix):
    files = glob.glob(prefix)
    files.sort()
    fileLength = len(files)
    
    baseFolderPath, baseFolderName = os.path.split(folderName)

    folderpath = os.path.join(baseFolderPath, baseFolderName+'-res')
    try:
        os.mkdir(os.path.join(baseFolderPath, baseFolderName+'-res'))
    except FileExistsError:
        pass
 
    filesInResFolder = os.listdir(folderpath)

    skipframesfreq = int(input('Skip frames:'))

    pbar = tqdm.tqdm(total=len(files))
    for i, fileName in enumerate(files):
        if i % skipframesfreq != 0: continue
        createImage(folderpath, fileName, i, filesInResFolder, fileLength)
        pbar.update(skipframesfreq)

    pbar.close()
    print('Output:', folderpath)

def convertFolder(foldername):
    saveAllImages(foldername,os.path.join(foldername,'*.asc'))
