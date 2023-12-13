import math
import tqdm
from .loader import loadASCIIFile, getSortedFolder, createFolder
from .png import createImage, loadFile, mapColor
from PIL import Image
import numpy as np
from math import inf
from random import randint, shuffle
import os
import openpyxl as pxl
from .gui import choiceMask
from _thread import start_new_thread
import time
import sys
import pyglet as pg

WHITE = (255,255,255,255)
RED = (255,0,0,255)
BLUE = (0,0,255,255)
GREEN = (0,255,0,255)
BLACK = (0,0,0,255)

# generate colors
COLORS = [[randint(0,255),randint(0,255),randint(0,255),255] for _ in range(200)]

def saveMask(mask, fname="mask.png"):
    
    imarr = []
    for row in mask:
        imarr.append([])

        for val in row:

            color = WHITE
            if val == -1:
                color = BLACK
            
            elif val == 1:
                color = RED
            elif val == 2:
                color = BLUE
            elif val == 3:
                color = GREEN
            elif val > 3:
                color = COLORS[val]

            imarr[-1].append(color)

    im = Image.fromarray(np.array(imarr, np.uint8))
    im.save(os.path.join('debug',fname))



def maskGetBbox(mask, needle=0):
    mn = [inf,inf]
    mx = [0,0]
    for i, row in enumerate(mask):
        for j, val in enumerate(row):
            
            if val != needle:
                mn[0] = min(mn[0], i)
                mn[1] = min(mn[1], j)
                mx[0] = max(mx[0], i)
                mx[1] = max(mx[1], j)

    # apply
    mask = [[val for val in row[mn[1]:mx[1]]] for row in mask[mn[0]:mx[0]]]
    return mask, mn, mx


def isolateValue(data, maxTemp, imarr=None, color=RED) -> list:
    mask = [[0 for _ in range(len(data[0]))] for _ in range(len(data))]
    for colNum in range(len(data[0])):

        lastTemp = None
        for rowNum in range(len(data)):
            temp = data[rowNum][colNum]

            if not lastTemp:
                lastTemp = temp
                continue

            if maxTemp < temp:
                if imarr: imarr[rowNum][colNum] = color
                mask[rowNum][colNum] = 1

    return mask


def filteroutLineNoise(mask, negative=0):
    lineLengths = [len([val for val in row if val]) for _, row in enumerate(mask)]
    # minLines = min(lines)
    maxLines = max(lineLengths)

    for rowNum, row in enumerate(mask):

        colors = {} # "coolors" men egentlig marks

        # hvilken farve er der mest af
        for mark in row:
            
            if mark in colors:
                colors[mark] += 1
            else:
                colors[mark] = 1

        colors = [(color, colors[color]) for color in colors]

        mostFrequentColor, lineLength = sorted(colors, key=lambda x: x[1])[-1]

            # print(lineLength, maxLines * .25, lineLength < maxLines * .25)
        if lineLength < maxLines * .90:
            mask[rowNum] = [negative for _ in mask[rowNum]]
        else:
            mask[rowNum] = [mostFrequentColor for _ in mask[rowNum]]

    return mask



def createMaskFromFrame(fpath, shape:tuple=(100,50), folder:str="debug", fingers:str=4):
    try:
        return __createMaskFromFrame(fpath, shape, folder, fingers)
    except Exception as e:
        pass


def __createMaskFromFrame(fpath, shape:tuple, folder, fingers):
    # make folder for debugging
    folder = os.path.join('mask',folder)
    
    try:
        os.mkdir(os.path.join('debug',folder))
    except FileExistsError:
        pass

    data, minTemp, maxTemp = loadASCIIFile(fpath)
    startSize = (len(data[0]),len(data))
    imarr = [[WHITE for _ in range(len(data[0]))] for _ in range(len(data))]


    ### STEP 1 ###
    # get warm spots
    diff = (maxTemp - minTemp) * 0.75
    mask = isolateValue(data, maxTemp - diff, imarr)
    mask, warmMaskMin, warmMaskMax = maskGetBbox(mask) #+ cropping
    saveMask(mask, os.path.join(folder,'mask-1.png'))

    ### STEP 2 ###
    # find bottom and top line if is in threadshold of average line length times coeffecient
    lineLengths = []
    for row in mask:
        line = [i for i in row if i]
        lineLength = len(line)
        if lineLength > 5: #filter out dead pixels
            lineLengths.append(lineLength)

    avgLineWidth = sum(lineLengths) / len(lineLengths)
    acceptLineCoeff = 1.25

    topLineIndex = inf
    bottomLineIndex = 0
    for i, line in enumerate(lineLengths):
            
        if line*acceptLineCoeff < avgLineWidth:
            topLineIndex = min(i, topLineIndex)
            bottomLineIndex = max(i, bottomLineIndex)

    # get height off mask
    pixelHeight = bottomLineIndex - topLineIndex
        

    ### STEP 3 ###    
    # get left most line
    lineLengths = []
    for colNum in range(len(mask[0])):
        line = [1 for rowNum in range(len(mask)) if mask[rowNum][colNum]]
        lineLength = len(line)
        if lineLength > 5: #filter out dead pixels
            lineLengths.append(lineLength)

    avgLineWidth = sum(lineLengths) / len(lineLengths)
    acceptLineCoeff = 1

    leftLineIndex = inf
    for i, line in enumerate(lineLengths):
            
        if line*acceptLineCoeff < avgLineWidth:
            leftLineIndex = min(i, topLineIndex)
        
    # add
    leftLineIndex += 20

    ### STEP 4 ###
    # find laser center
    diff = (maxTemp - minTemp) * 0.1
    mask = isolateValue(data, maxTemp - diff, imarr, BLUE)
    mask, laserMaskMin, laserMaskMax = maskGetBbox(mask)
    
    saveMask(mask, os.path.join(folder,'mask-2.png'))

    # make lines, laser burde være en cirkel. Linjer burde være uafbrudte
    maxLine = (0, 0, 0) # (pos, val, center)
    for rowNum, row in enumerate(mask):
        
        lineLength = 0
        for colNum, val in enumerate(row):

            if lineLength > 0 and not val: # startet og afbrudt
                break
            
            if val: lineLength += 1

        if lineLength > maxLine[1]:
            maxLine = (rowNum,lineLength, colNum-lineLength//2)


    ### STEP 5 ###
    # assume length 
    ratio = shape[0] / shape[1]
    topPos = (warmMaskMin[1]+leftLineIndex, warmMaskMin[0])
    bottomPos = (int(warmMaskMin[1]+ pixelHeight * ratio), int(warmMaskMin[0] + pixelHeight))
    
    im = Image.fromarray(np.array(imarr, np.uint8))
    laserTopPos = topPos
    im = im.crop((*topPos, *bottomPos))
    im.save(os.path.join('debug',folder,'test.png'))

    # im = Image.open('irdata_0011_0100.png')
    # im = im.crop((*topPos, *bottomPos))
    # im.save(os.path.join('files','test-img-crop.png'))

    # half 
    topPos = (int(warmMaskMin[1]+leftLineIndex+(pixelHeight * ratio)//2), int(warmMaskMin[0]))

    # add padding
    padding = 10
    topPos = (topPos[0]+padding, topPos[1]+padding)
    bottomPos = (bottomPos[0]-padding, bottomPos[1]-padding)
    offset = topPos

    # im = Image.open('irdata_0011_0100.png')
    # im = im.crop((*topPos, *bottomPos))
    # im.save('test-img-crop-right.png')

    ### STEP 6 ###
    # get carbon black / metallic surface
    data = [[val for val in row[topPos[0]:bottomPos[0]]] for row in data[topPos[1]:bottomPos[1]]]
    # data.reverse() # NOTE: SLET
    mask = [[0 for _ in range(len(data[0]))] for _ in range(len(data))]
    for colNum in range(len(data[0])):
        
        line = [data[rowNum][colNum] for rowNum in range(len(data))]
        avgTemp = sum(line) / len(line)
        # maxTemp = max(line)
        # minTemp = min(line)

        # boxNum = 1
        for rowNum in range(len(data)):
            temp = data[rowNum][colNum]                

            if temp > avgTemp:
            
                # if rowNum > 0 and mask[rowNum-1][colNum] == 0:
                #     boxNum += 1
                
                mask[rowNum][colNum] = 1 # boxNum
                
        # print(minTemp, avgTemp, maxTemp)
    
    saveMask(mask, os.path.join(folder,'mask-area.png'))

    filteroutLineNoise(mask, 0)

    saveMask(mask, os.path.join(folder,'mask-filter-noise.png'))

    # count boxes
    box = 0
    lastMark = inf
    for row in mask:
        mark = row[0]

        if mark != lastMark: #change
            box += 1
        
        lastMark = mark
    
    # rule
    if box != fingers:
        return None

    # saveMask(mask, 'mask-box.png')
    
    # add mask into full context
    fullmask = [[-1 for _ in range(startSize[0])] for _ in range(startSize[1])]

    for row in range(startSize[1]):

        if not(offset[1] < row < offset[1]+len(mask)):
            continue
        
        for col in range(offset[0], offset[0]+len(mask[0])):
            fullmask[row][col] = mask[row-offset[1]][col-offset[0]]

    saveMask(fullmask, os.path.join(folder,'mask-full.png'))

    #print(laserMaskMin[1] + (laserMaskMax[1] - laserMaskMin[1])//2, pixelHeight//2)

    laseroff = laserMaskMax[1] - laserTopPos[1] + (laserMaskMax[1] - laserMaskMin[1])//2

    return fullmask, laseroff - pixelHeight//2


def createAndOverlayMasks(fpath:str, fingers:int=4, maskheapsize:int=10) -> None:

    createFolder(os.path.join('debug','mask'))

    files = getSortedFolder(os.path.join(fpath, '*.asc'))

    files = files[round(len(files)*.2):round(len(files)*.8)]

    # hvis en frame er dødt skal alt nok gå
    # da vi tager 10 forskellige frames og laver masker til alle
    # så burde alt andet gå mega stærkt
    
    # create mask
    masks = []
    pbar = tqdm.tqdm(total=maskheapsize, desc="Laver maske")
    i = 0
    c = 0
    laseroffsetsum = 0 
    while c < maskheapsize:
        file = files[randint(0,len(files)-1)]
        i += 1
        res = createMaskFromFrame(file, fingers=fingers, folder="mask-{}-{}".format(str(c),str(i)))
        if res:
            masks.append(res[0])
            laseroffsetsum += res[1]
            pbar.update()
            c += 1

    laseroffsetavg = laseroffsetsum / 10
    print('\033[91mDer ser ud til at laseren er forskudt med {}px \033[0m'.format(laseroffsetavg))
    if input('Skal dette ændres? [Y/N] ').lower() != 'y':
        laseroffsetavg = 0
    else:
        print('Dette blive ændret')

    pbar.close()

    # filter masks
    # print('\033[93m','{} Bad frame, results may be inaccurate'.format(len([mask for mask in masks if not mask])), '\033[0m')
    masks = [mask for mask in masks if mask]

    # overlay masks
    fmask = [[{0:0} for j in i] for i in masks[0]]
    for rowNum, row in enumerate(fmask):

        for colNum in range(len(row)):
            
            for mask in masks:

                val = mask[rowNum][colNum]
                mark = fmask[rowNum][colNum]

                if val in mark.keys():
                    mark[val] += 1

                else:
                    mark[val] = 0


    mask = [[0 for j in i] for i in masks[0]]
    # overlay
    for rowNum, row in enumerate(mask):

        for colNum in range(len(row)):

            mark = fmask[rowNum][colNum]
            maxKey = max([(mark[key], key) for key in mark], key=lambda x: x[0])
            mask[rowNum][colNum] = maxKey[1]

    saveMask(mask, 'mask.png')

    # count boxes and add padding
    box = 0
    cmask, offset, _ = maskGetBbox(mask, -1)
    filteroutLineNoise(cmask)
    newmask = [[] for _ in cmask]
    lastMark = None

    paddingCoeff = 0.3 # skal være under 0.5

    maxPadding = 20
    lastChange = 0
    for rowNum, row in enumerate(cmask):
        
        mark = row[0]

        if mark != lastMark: #change
            box += 1

            if lastChange != rowNum:
                
                padding = min(maxPadding, round(abs(rowNum - lastChange) * paddingCoeff))
                print('Padding:',padding)
                for i in range(lastChange, lastChange+padding):
                    newmask[i] = [0 for _ in row]
                for i in range(rowNum-padding, rowNum):
                    newmask[i] = [0 for _ in row]

                lastChange = rowNum

        newmask[rowNum] = [box for _ in row]
        lastMark = mark

    # add last padding and last box
    padding = min(maxPadding, round(abs(rowNum - lastChange) * paddingCoeff))
    print('Padding:',padding)
    for i in range(lastChange, lastChange+padding):
        newmask[i] = [0 for _ in row]
    for i in range(rowNum-padding, rowNum+1):
        newmask[i] = [0 for _ in row]

    mask = newmask

    saveMask(mask, 'mask-cato.png')

    return mask, (offset[0]-round(laseroffsetavg), offset[1])


def getTempFromFrameWithMask(fpath, mask, maskpos):
    try:
        return __getTempFromFrameWithMask(fpath, mask, maskpos)
    except Exception as e:
        print('\033[93m','Bad frame, skipping {}'.format(fpath), '\033[0m')
        return False


def __getTempFromFrameWithMask(fpath, mask, maskpos):
    data, minTemp, maxTemp = loadASCIIFile(fpath)
    
    temps = {}
    #img = [[0 for _ in row] for row in mask]
    for colNum in range(maskpos[1], len(mask[0])+maskpos[1]):
        
        temp = {}
        
        for rowNum in range(maskpos[0], len(mask)+maskpos[0]):
            
            mark = mask[rowNum-maskpos[0]][colNum-maskpos[1]]
            
            if mark not in temp.keys(): temp[mark] = [0,0]

            temp[mark][0] += 1
            temp[mark][1] += data[rowNum][colNum]

        temps[colNum-maskpos[1]] = temp

    # calculate average
    for key in temps:
        
        for i in temps[key]:
            temps[key][i] = temps[key][i][1] / temps[key][i][0]

    
    # gør det igen jf. filtrerings algoritmen
    span = [-50, 50]
    res = {}
    for colNum in range(maskpos[1], len(mask[0])+maskpos[1]):
        
        temp = {}
        
        for rowNum in range(maskpos[0], len(mask)+maskpos[0]):
            
            i = colNum-maskpos[1]
            mark = mask[rowNum-maskpos[0]][i]
            
            if mark not in temp.keys(): temp[mark] = [0,0]

            # filter
            if not (temps[i][mark] + span[0] < data[rowNum][colNum] < temps[i][mark] + span[1]):
                continue

            temp[mark][0] += 1
            temp[mark][1] += data[rowNum][colNum]

        res[i] = temp

    # average igen igen
    for key in res:
        
        for i in res[key]:
            res[key][i] = res[key][i][1] / res[key][i][0]

    return res

def rule(ts) -> list:
    res = []

    for x in ts:
        
        r = []
        for key in sorted(ts[x].keys()): # alle frames burde have lige mange keys, da de kører samme maske
            if key == 0: continue # ingen grund til at tage padding imellem med
            r.append(ts[x][key])
        
        if len(r) != 4:
            continue
        
        res.append(r)

    return res


def get_color(colorRGBA1, colorRGBA2):
    #https://stackoverflow.com/questions/52992900/how-to-blend-two-rgb-colors-front-and-back-based-on-their-alpha-channels
    alpha = 255 - ((255 - colorRGBA1[3]) * (255 - colorRGBA2[3]) / 255)
    red   = (colorRGBA1[0] * (255 - colorRGBA2[3]) + colorRGBA2[0] * colorRGBA2[3]) / 255
    green = (colorRGBA1[1] * (255 - colorRGBA2[3]) + colorRGBA2[1] * colorRGBA2[3]) / 255
    blue  = (colorRGBA1[2] * (255 - colorRGBA2[3]) + colorRGBA2[2] * colorRGBA2[3]) / 255
    return (int(red), int(green), int(blue), int(alpha))


def createPreviewMaskImage(mask, maskpos, file, outputfolder='debug'):
    fname = createImage(outputfolder, file)

    im = Image.open(fname)
    imarr = np.array(im)
    im.close()
    os.remove(fname)

    for rowNum, row in enumerate(imarr):

        if not(maskpos[0] < rowNum < maskpos[0]+len(mask)):
            continue

        for colNum, color in enumerate(row):

            if not(maskpos[1] < colNum < maskpos[1]+len(mask[0])):
                continue

            if mask[rowNum - maskpos[0]][colNum - maskpos[1]] == 0:
                continue

            cl = (255,0,0,100)

            imarr[rowNum][colNum] = get_color(color, cl)

    Image.fromarray(imarr).save(os.path.join(outputfolder,os.path.split(file)[-1].replace('.asc', '.png')))


def retrieveTempFromFiles(files, mask, maskpos, outputfolder):
    outputfolder = os.path.join(outputfolder, 'temperature')
    createFolder(outputfolder)
    pbar = tqdm.tqdm(total=len(files), desc="Beregner temperatur")

    workbook = pxl.Workbook()
    sheet = workbook.active
    table = []
    
    freq = 10
    saveFreq = freq*1000
    previewFreq = 1000

    for i, file in enumerate(files):
        pbar.update()

        if (i+1) % saveFreq == 0:
            workbook.close()
            workbook.save(os.path.join(outputfolder,str(int(i/saveFreq))+'.xlsx'))
            workbook = pxl.Workbook()
            sheet = workbook.active
        
        if i % previewFreq == 0:
            createPreviewMaskImage(mask, maskpos,file, os.path.join('debug', 'mask'))

        if not (i % freq == 0):
            continue

        res = getTempFromFrameWithMask(file, mask, maskpos)
        if not res: continue
        r = rule(res)

        for o in r: sheet.append([*o])
        for o in r: table.append([*o])

    pbar.close()

    workbook.save(os.path.join(outputfolder,str(math.ceil(i/saveFreq))+'.xlsx'))
    workbook.close()

    print('Output:', outputfolder)

    return table


def analyzeFromFolder(fpath:str, baseoutputfolder:str="files", fingers=4, maskheapsize:int=10) -> list:
    mask, maskpos = createAndOverlayMasks(fpath, fingers, maskheapsize)
    files = getSortedFolder(os.path.join(fpath, '*.asc'))

    outputfolder = os.path.join(baseoutputfolder, os.path.split(fpath)[-1]+'-res')
    retrieveTempFromFiles(files, mask, maskpos, outputfolder)
    

global_mask = [None]

def drawBox(mask, x, y, width, height, cl=1) -> list:
    
    for rowNum, row in enumerate(mask):

        if not (y < rowNum < y + height):
            continue

        for colNum in range(len(row)):

            if x < colNum < x + width:
                mask[rowNum][colNum] = cl


def analyzeFromFolderHeavyWork(files, baseoutputfolder, fpath):
    
    while not global_mask[0]:
        time.sleep(1)
        pass
    
    if global_mask[0] == -1:
        return

    data = loadFile(files[0])[0]
    mask = [[0 for _ in row] for row in data]

    # create mask
    boxes = global_mask[0]

    xborder = [-inf,inf]
    yborder = [inf, -inf]
    for i,box in enumerate(boxes):
        x1 = min(box.x, box.x+box.width)
        x2 = max(box.x, box.x+box.width)
        y1 = min(len(mask)-box.y, len(mask)-box.y-box.height) #pyglet coord -> pixel coord
        y2 = max(len(mask)-box.y, len(mask)-box.y-box.height)

        drawBox(mask, x1, y1, x2-x1, y2-y1, i+1)

        yborder = (
            min(yborder[0], y1, y2),
            max(yborder[1], y1, y2),
        )

        xborder = (
            max(xborder[0], x1),
            min(xborder[1], x2),
        )

    saveMask(mask, 'mask-test-manual.png')
    mask = [[val for val in row[xborder[0]:xborder[1]]] for row in mask[yborder[0]:yborder[1]]]
    saveMask(mask, 'mask-test-manual-crop.png')
    maskpos = yborder[0], xborder[0]

    outputfolder = os.path.join(baseoutputfolder, os.path.split(fpath)[-1]+'-res')
    retrieveTempFromFiles(files, mask, maskpos, outputfolder)
    
    pg.app.exit()


def analyzeFromFolderManual(fpath:str, baseoutputfolder:str="files") -> list:
    # mask, maskpos = createAndOverlayMasks(fpath, fingers, maskheapsize)
    files = getSortedFolder(os.path.join(fpath, '*.asc'))

    start_new_thread(analyzeFromFolderHeavyWork, (files,baseoutputfolder, fpath))

    choiceMask(files[randint(0,len(files)-1)], global_mask)
