
#https://www.engineersedge.com/heat_transfer/thermal_diffusivity_table_13953.htm

import numpy as np
from model import *
import kaxe
import math
import tqdm

# SETTINGS["MINTEMP"] = -10
# SETTINGS["MAXTEMP"] = 5000

def createPlot(temps):
    try:
        plot = kaxe.Plot([0,300, 0, 200])

        x = [i[0] for i in temps if (i[1] > 0 and not math.isnan(i[1]))]
        y = [i[1] for i in temps if (i[1] > 0 and not math.isnan(i[1]))]

        points = kaxe.Points(x,y).legend('Gnm temperatur')
        plot.add(points)

        # reg = kaxe.regression(lambda x, a, b: a + b*np.log(x), x, y)
        # func = kaxe.Function(lambda x: reg[0][0]+reg[0][1]*np.log(x)).legend('Regression')
        a, b, c, d = kaxe.regression(lambda x, a, b, c, d: a*x**3 + b*x**2 + c*x + d, x, y)[0]
        print(a,b,c,d)
        func = kaxe.Function(lambda x: a*x**3 + b*x**2 + c*x + d, x, y).legend('Regression')
        plot.add(func)
        
        plot.save('plot-test.png')

    except Exception as e:
        print(e)


def createPlotCompare(vals):
    try:
        plot = kaxe.Plot([0,310, -8, 2])

        x = [i[0] for i in vals]
        y = [i[1] for i in vals]

        points = kaxe.Points(x,y).legend('Gnm temperatur forskel')
        plot.add(points)

        # reg = kaxe.regression(lambda x, a, b: a + b*np.log(x), x, y)
        # func = kaxe.Function(lambda x: reg[0][0]+reg[0][1]*np.log(x)).legend('Regression')
        
        plot.save('plot-test-compare.png')

    except Exception as e:
        print(e)



size = (36, 33)
a, b, c, d = 1.3290929931368414e-05, -0.00995249804889889, 2.6347917379009598, -0.5985274240764386
fps = 50
def runModel():
    #center = (size[0]//2, size[1]//2)
    laser = (size[0]*78/(427/2), size[1]*0.44)

    #mesh = [[0 for _ in range(size[0])] for _ in range(size[1])]
    mesh = loadFrame('start_frame.asc')
    # mesh = loadMesh('16000-40,0.asc')

    mesh = [[temp for i,temp in enumerate(row) if i % 6 == 0] for j, row in enumerate(mesh) if j % 6 == 0]
    #print(len(mesh), len(mesh[0]))

    # model = HeatEquationModel(mesh, timeStep=0.0025, sizeStep=0.002, diffusionConstant=4.075*10**(-6))
    model = HeatEquationModel(mesh, timeStep=0.0050, sizeStep=(100/size[0])/1000, diffusionConstant=4.2*10**(-6))
    model.setSaveSettings(folderNamePath='res', saveFreq=100, relativeScale=False, toImage=False)

    effect = 110
    source = HeatSource(model, effect=effect, heatCapacity=500, density=8)
    source.circle(laser, 22)
    source.run()

    model.addCorectionFunction(lambda t, T: a*t**3 + b*t**2 + c*t + d)
    model.runUntilTime(350)

def testCorrectionFunction():
    
    #plot = kaxe.Plot([0,100, 0, 150])
    plot = kaxe.Plot()

    x0 = []
    y0 = []

    for i in getSortedFolder('res/*.asc'):
        data = loadASCII(i)
        simTemp = sum([sum(i) for i in data["map"]])
        simTemp = simTemp / (len(data["map"]) * len(data["map"][0]))
        time = data["time"]
        x0.append(time)
        y0.append(simTemp)
    
    p = kaxe.Points(x0, y0, connect=True).legend('Data')

    func = kaxe.Function(lambda x: a*x**3 + b*x**2 + c*x + d).legend('Regression')

    plot.add(p)
    plot.add(func)

    plot.save('correction-test.png')

def getAvgTemperaturePerFrame():
    
    temps = []
    freq = 100
    plotFreq = 100 * freq

    for i,file in enumerate(getSortedFolder('forsøg/*.asc', key=lambda fname: int(fname.split('.')[0].replace('irdata_','', 1).replace('_', '', -1)))):

        if (i+1) % plotFreq == 0:
            createPlot(temps)

        if (i+1) % freq != 0:
            continue

        timestamp = file.split('/')[-1].split('.asc')[0].replace('irdata_', '').split('_')
        timestamp = ((int(timestamp[0]) - 1) * 2000 + int(timestamp[1])) / fps

        # if timestamp < 24:
        #     continue
        # timestamp -= 24

        data = loadFrame(file)
        convertFramesToImages([data], ["test.png"], strictNames=True)
        sumTemp = sum([sum(row) for row in data])
        avgTemp = sumTemp / (len(data[0])*len(data))
        temps.append((timestamp, avgTemp))
        print(file, avgTemp, timestamp)

        #convertFramesToImages([data], ['test.png'], True, strictNames=True)

    createPlot(temps)


def loadFrame(fname):
    
    cbcol = [126, 350]
    cbrow = [126, 325]

    data = loadASCII(fname, 'ISO 8859-1', 'Data')["map"]
    data = [[temp for colNum, temp in enumerate(row) if cbcol[0] < colNum < cbcol[1]] for rowNum, row in enumerate(data) if cbrow[0] < rowNum < cbrow[1]]

    return data


def compareFrames():
    res = []

    s1 = (198, 223)
    s2 = size

    folder = 'compare'

    def translate(i,j):
        #print(i, j, math.floor((s2[0] / s1[0]) * i), math.floor((s2[1] / s1[1]) * j))
        return math.floor((s2[0] / s1[0]) * i), math.floor((s2[1] / s1[1]) * j)

    d2files = getSortedFolder('res/*.asc')
    filepointer = 0

    freq = 100
    saveFreq = 100 * freq

    files = getSortedFolder('forsøg/*.asc', key=lambda fname: int(fname.split('.')[0].replace('irdata_','', 1).replace('_', '', -1)))
    bar = tqdm.tqdm(total=len(files))

    for fileNum, file in enumerate(files):
        
        if fileNum % saveFreq == 0:
            createPlotCompare(res)
        
        if fileNum % freq != 0:
            continue

        d1 = loadFrame(file)

        timestamp = file.split('/')[-1].split('.asc')[0].replace('irdata_', '').split('_')
        timestamp = ((int(timestamp[0]) - 1) * 2000 + int(timestamp[1])) / fps

        for dflnum in range(filepointer, len(d2files)):
            dfl = d2files[dflnum]

            val = float(dfl.split('.asc')[0].split('-')[1].replace(',', '.'))
            if val > timestamp:
                filepointer = dflnum
                break

        d2 = loadASCII(dfl)["map"]

        s = 0
        ddiff = [[0 for _ in row] for row in d1]
        for rowNum, row in enumerate(d1):

            for colNum in range(len(row)):
                
                i, j = translate(rowNum, colNum)
                # s += abs(d1[rowNum][colNum] - d2[i][j])
                s += d1[rowNum][colNum] - d2[i][j]
                ddiff[rowNum][colNum] = d1[rowNum][colNum] - d2[i][j]

        avg = s / (len(d1) * len(d1[0]))
        
        f1 = '{}/{}'.format(folder, '{}-f.png'.format(str(timestamp)))
        f2 = '{}/{}'.format(folder, '{}-s.png'.format(str(timestamp)))
        fdiff = '{}/{}'.format('diffmap', '{}.png'.format(str(timestamp)))
        
        d2 = np.rot90(d2)
        convertFramesToImages([d1, d2, ddiff], [f1, f2, fdiff], strictNames=True)

        res.append((timestamp, avg))
        bar.update(freq)
    
    createPlotCompare(res)
    bar.close()


def main():
    runModel_ = False

    #data = loadFrame('forsøg/irdata_0006_0547.asc')
    #convertFramesToImages([data], ['test.png'], True, strictNames=True)

    # getAvgTemperaturePerFrame()
    # return

    #runModel_ = True
    liveView = True

    if runModel_:
        if liveView:
            liveViewer(size,'res', ASCII=True)
            runModel()
            closeLiveViewer()
        else:
            runModel()
        #return

    # test
    testCorrectionFunction()
    compareFrames()

if __name__ == '__main__':
    main()