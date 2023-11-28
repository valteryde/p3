
import math
import glob, os

def loadASCIIFile(fileName:str) -> list:
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