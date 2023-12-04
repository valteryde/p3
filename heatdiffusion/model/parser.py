
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import math
import glob
try:
    import moviepy.video.io.ImageSequenceClip
except ImportError:
    print('Video compiling is not avaliable')
from .map import heatmap

COLORCHECKPOINTS = heatmap

SETTINGS = {
    "MINTEMP" : 0,
    "MAXTEMP" : 400
}

def mapTempToColor(col, mn=None, mx=None):
    if mn is None: mn = SETTINGS["MINTEMP"]
    if mx is None: mx = SETTINGS["MAXTEMP"]

    if -0.005 < mn - mx < 0.005:
        return COLORCHECKPOINTS[-1]

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

BLACK = (0,0,0,255)

def addScale(image, minTemp, maxTemp, width, height, offset):
    
    draw = ImageDraw.Draw(image)

    padding = 1
    totalSteps = height - 2*padding
    size = maxTemp - minTemp
    stepSize = size / totalSteps
    l = [[mapTempToColor(minTemp + stepSize * i, minTemp, maxTemp)]*(width-padding*2) for i in range(totalSteps)]

    l.reverse()

    colorImage = Image.fromarray(np.array(l, np.uint8))
    
    draw.rectangle((*offset, width+offset[0], height+offset[1]), fill=(255,255,255,255))
    
    # draw.text((offset[0],offset[1]-10), str(round(maxTemp,1)), fill=BLACK)
    # draw.text((offset[0],offset[1]+height), str(round(minTemp,1)), fill=BLACK)

    image.paste(colorImage, (padding+offset[0],padding+offset[1]))

def convertFramesToImages(frames:list, names:list, relativeTempScale:bool=False, showScale:bool=False, strictNames:bool=False):
    
    #folderNumber = max([*[int(i) for i in os.listdir('res') if os.path.isdir(os.path.join('res', i))], 0])+1
    #folderName = os.path.join('res',str(folderNumber))
    
    folderName = 'res'

    pixelFrames = []

    for num, frame in enumerate(frames):
        pixelFrames.append([])

        # find min & max
        if relativeTempScale:
            minTemp = min([min(row) for row in frame])
            maxTemp = max([max(row) for row in frame])

        for row in frame:
            pixelFrames[-1].append([])

            for val in row:
                
                if relativeTempScale:
                    pixelFrames[-1][-1].append(mapTempToColor(val, minTemp, maxTemp))
   
                else:
                    pixelFrames[-1][-1].append(mapTempToColor(val))

    
    for num, frame in enumerate(pixelFrames):
        
        if showScale:
            # add padding in right side
            frame = [[*row, *[[255,255,255,255]]*10] for row in frame]

        arr = np.array(frame, dtype=np.uint8)

        im = Image.fromarray(arr)
        
        if showScale:
            addScale(im, minTemp, maxTemp, 10, len(frame)-10, (len(frame[0])-10, 5))

        if strictNames:
            im.save(names[num])
            continue
        
        im.save(os.path.join(folderName, '{}.png'.format(str(names[num]).replace('.',','))))


def convertFramesToASCII(frames:list, names, **data):
    
    asciiFrames = []

    """
    
    [settings]
    tid = 10
    hej = 5
    wow = 1
    
    [en anden blok] <-- eventuelt kan en anden blok også ligges derinde

    [map]
    0   1   31  21  0   21
    2   51  2   0   1   0  
    4   0   0   0   1   0
    20  0   6   7   9   8
    """

    folderName = 'res'


    for num, frame in enumerate(frames):
        
        # string map
        smap = ''
        ssettings = ''


        asciiFrames.append([])

        for row in frame:

            for val in row:
                smap += '{}\t'.format(val)
            
            smap += '\n'

        file = open(os.path.join(folderName, '{}.asc'.format(str(names[num]).replace('.', ','))), 'w')

        file.write('[SETTINGS]\n')
        file.write(ssettings)
        file.write('[MAP]\n')
        file.write(smap)
        file.close()


def makeVideo():

    image_folder='res'
    fps=5

    image_files = [os.path.join(image_folder,img)
                for img in os.listdir(image_folder)
                if img.endswith(".png")]
    
    image_files.sort(key=lambda p: int(os.path.split(p)[-1].split('.')[0]))
    
    clip = moviepy.video.io.ImageSequenceClip.ImageSequenceClip(image_files, fps=fps)
    clip.write_videofile('video.mp4', codec='mpeg4')

def mapColor(data, minTemp, maxTemp):

    # make pixels
    for rowNum, row in enumerate(data):
        
        for colNum, col in enumerate(row):
            data[rowNum][colNum] = mapTempToColor(col, minTemp, maxTemp)
    
    return np.array(data, np.uint8)


def loadMesh(fname:str) -> list:
    return loadASCII(fname)["map"]



# DATABEHANDLING
def getSortedFolder(pattern, key:callable=None):

    files = glob.glob(pattern)
    fileKeyList = []
    for file in files:
        fname = os.path.split(file)[-1] #index also == 1
        if key:
            fileKeyList.append((key(fname), file))
        else:    
            fileKeyList.append((int(fname.split('-')[0]),file))
    return [i[1] for i in sorted(fileKeyList, key=lambda x: x[0])]


def loadASCII(fname:str, encoding='utf-8', mapblock='MAP') -> dict:
    file = open(fname, 'r', encoding=encoding)
    txt = file.read()
    file.close()

    # get all blocks
    pointer = -1
    blocks = [] # fx {"name": "settings", "data": ...}
    for i, c in enumerate(txt):

        if c == '[':
            if pointer == -1:
                pointer = i
                continue
            
            blocks[-1]["data"] = txt[pointer+len(blocks[-1]["name"])+2:i]
            pointer = i

        elif c == ']':
            blocks.append({"name":txt[pointer+1:i]})

    blocks[-1]["data"] = txt[pointer+len(blocks[-1]["name"])+2:]
    blocks = {i["name"]:i["data"] for i in blocks}
    
    # find map block
    lmap = [[float(j.replace(',', '.')) for j in i.split('\t') if j] for i in blocks[mapblock].split('\n') if i]
    
    try:
        tme = float(os.path.split(fname)[-1].split('.asc')[0].split('-')[-1].replace(',','.'))
    except Exception:
        tme = None

    return {"map": lmap, "time": tme}

