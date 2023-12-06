
import math
import glob, os
import shutil
import codecs

def createFolder(folder, remove:bool=True):
    try:
        if remove:
            shutil.rmtree(folder)
    except FileNotFoundError:
        pass
    try:
        os.mkdir(folder)
    except FileExistsError:
        pass

def saveASCIIFile(fname, data, settings):
    
    file = open(fname, '+bw')
    file.write(codecs.encode(settings, errors="replace"))
    file.write(codecs.encode('[Data]\n', errors="replace"))
    file.write(codecs.encode('\r\n'.join(['\t'.join(row) for row in data]), errors="replace"))
    file.close()


def loadASCIIFile(fileName:str, getRaw=False) -> list:
    file = open(fileName, 'rb')
    data = file.read().decode('utf-8', 'replace')
    
    dataKeyword = '[Data]'
    dataIndex = data.index(dataKeyword)
    settings = data[:dataIndex]
    data = data[dataIndex+len(dataKeyword):]
    data = data.encode('utf-8')

    data = data.split(b'\r\n')
    data.pop(0)

    highestTemp, lowestTemp = 0, math.inf
    for rowNum, row in enumerate(data): # in place (almost)

        if not row or row == " ":
            continue
        
        data[rowNum] = [float(i.replace(b',', b'.')) for i in row.split(b'\t') if i]
        highestTemp = max(*data[rowNum], highestTemp)
        lowestTemp = min(*data[rowNum], lowestTemp)

    data.pop(-1)

    if getRaw:
        return data, lowestTemp, highestTemp, settings
    return data, lowestTemp, highestTemp


def getSortedFolder(pattern):
    files = glob.glob(pattern)
    fileKeyList = []
    for file in files:
        fname = os.path.split(file)[-1] #index also == 1
        fname = ''.join([i for i in fname if i in '0123456789'])
        if not fname:
            fname = '-1'
        fileKeyList.append((int(fname.split('_')[0]),file))
    return [i[1] for i in sorted(fileKeyList, key=lambda x: x[0])]