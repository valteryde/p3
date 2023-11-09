
import math
from PIL import Image
import numpy as np
import platform
from tqdm import tqdm
import os
import logging
import glob
from .loader import loadASCIIFile
import openpyxl as pxl

debugOn = False

### ONLY FOR TESTING ###
def loadImage(fname): # grayscale
    im = Image.open(fname)
    arr = np.array(im)

    l = []
    for i, row in enumerate(arr):
        l.append([])
        for j, _ in enumerate(row):
            l[-1].append((arr[i][j][0]))

    return l


TOLERANCES = {
    "carbon_black_temp_diffrence": 10, 
    "background_temperature_diffrence": 100
}

WHITE = [255,255,255,255]
BLACK = [0,0,0,255]
RED = [255,0,0,255]

BACKGROUND = 0
SURFACE = 1
CARBONBLACK = 2

debugCount = 0
def analyzeFrame(data, debug:bool=debugOn) -> list:
    global debugCount
    if debug: previewImage = [[RED for i in range(len(data[0]))] for j in range(len(data))]

    mask = [[SURFACE for i in range(len(data[0]))] for j in range(len(data))]
    
    # find hottest point from every row
    hotRow = [max(i) for i in data]
    hotRow.sort()
    hotRow.reverse()
    maxTemp = sum(hotRow[:min(len(hotRow), 20)]) / min(len(hotRow), 20)

    coldRow = [min(i) for i in data]
    coldRow.sort()
    minTemp = sum(coldRow[:min(len(coldRow), 20)]) / min(len(coldRow), 20)

    # max is carbon black
    for rowNum, row in enumerate(data):

        for colNum, temp in enumerate(row):
            
            if temp > maxTemp - TOLERANCES["carbon_black_temp_diffrence"]:
                if debug: previewImage[rowNum][colNum] = BLACK
                mask[rowNum][colNum] = CARBONBLACK

    # min is background
    for rowNum, row in enumerate(data):

        for colNum, temp in enumerate(row):
            
            if temp < minTemp + TOLERANCES["background_temperature_diffrence"]:
                if debug: previewImage[rowNum][colNum] = WHITE
                mask[rowNum][colNum] = BACKGROUND

    if debug: Image.fromarray(np.array(previewImage, np.uint8)).save(os.path.join('debug','DEBUG-{}.png'.format(debugCount)))
    if debug: debugCount += 1
    return mask


def createMask(files, layers:int, procent:float=0.8, debug:bool=debugOn):
    files.sort()

    # get first 20 images to determine area
    layerRuns = min(layers, len(files))
    pbar = tqdm(desc="Maske",total=layerRuns)
    masks = []
    for file in files[:layerRuns]:
        masks.append(analyzeFrame(loadASCIIFile(file)[0], debug=True))
        pbar.update()
    
    pbar.close()

    # overlay and count
    res = [[BACKGROUND for j in range(len(masks[0][0]))] for i in range(len(masks[0]))]
    procHold = math.floor(procent * len(masks))
    surfacePos = [math.inf, math.inf, -1, -1] #row, col, row, col
    for row in range(len(masks[0])):
        
        for col in range(len(masks[0][0])):

            carbonCount = 0
            surfaceCount = 0
            for mask in masks:

                carbonCount += mask[row][col] == CARBONBLACK
                surfaceCount += mask[row][col] == SURFACE

            if carbonCount > procHold:
                res[row][col] = CARBONBLACK
            
            elif surfaceCount > procHold:
                res[row][col] = SURFACE

                surfacePos[0] = min(surfacePos[0], row)
                surfacePos[1] = min(surfacePos[1], col)
                surfacePos[2] = max(surfacePos[2], row)
                surfacePos[3] = max(surfacePos[3], col)


    # debug
    if not debug: return res, surfacePos

    debugImage = []
    for row in res:
        debugImage.append([])
        for cell in row:

            if cell == CARBONBLACK:
                debugImage[-1].append(BLACK)
            elif cell == SURFACE:
                debugImage[-1].append(RED)
            else:
                debugImage[-1].append(WHITE)

    if debug: Image.fromarray(np.array(debugImage, np.uint8)).save(os.path.join('debug','mask.png'))
    return res, surfacePos



def crop(data, pos):
    return [i[pos[1]:pos[3]]  for i in data[pos[0]:pos[2]]]


def getTempWithMask(data, mask, maskPos) -> list:
    data = crop(data, maskPos)

    carbonBlack = [0, 0]
    surface = [0, 0]

    for rowNum, row in enumerate(data):
        for colNum, temp in enumerate(row):
            
            if mask[rowNum][colNum] == SURFACE:
                carbonBlack[0] += temp
                carbonBlack[1] += 1
                
            elif mask[rowNum][colNum] == CARBONBLACK:
                surface[0] += temp
                surface[1] += 1
            
            else:
                continue
    
    if carbonBlack[1] == 0 or surface[1] == 0:
        return None

    return carbonBlack[0]/carbonBlack[1], surface[0]/surface[1]


def loadASCIIFile(*args):
    return [loadImage('test.png')]


def analyzeFromFolder(path):
    
    files = glob.glob(os.path.join(path,'*.asc'))
    mask, maskPos = createMask(files, 20)

    maskPos = [151, 120, 393, 387]
    pbar = tqdm(desc="Temperatur",total=len(files))

    res = []
    for file in files:
        res.append((os.path.split(file)[1],getTempWithMask(loadASCIIFile(file)[0], mask, maskPos)))
        pbar.update()

    pbar.close()

    # save to excel
    # Start by opening the spreadsheet and selecting the main sheet
    
    pathsplit = path.split(os.path.sep)
    basepath = os.path.sep.join(pathsplit[:-1])
    outputFileName = 'output-{}.xlsx'.format(pathsplit[-1])
    outPutPath = os.path.join(basepath, outputFileName)
    workbook = pxl.Workbook()
    sheet = workbook.active

    for name, temp in res:
        if not temp: continue
        sheet.append([name, *temp])

    # Save the spreadsheet
    workbook.save(filename=outPutPath) # not saving the correct place, FIXED
    print('Output: {}'.format(outPutPath))
