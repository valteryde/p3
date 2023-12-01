
from model import HeatEquationModel
from model import HeatSource
from model import SETTINGS, convertFramesToImages
from model import loadMesh, getSortedFolder, loadASCII
from model import liveViewer, closeLiveViewer
import numpy as np
import kaxe
import math

EFFECT = 400
SIZE = (25,25) # width, height
CENTER = (SIZE[0]//2, SIZE[1]//2)

MESHPATH = '160000-800,0.asc'
HEATCAPACITY = 500
DENSITY = 8
TIMESTEP = 0.0025
SIZESTEP = 0.004
DIFFUSIONCONSTANT = 4.2*10**(-6)
LASERRADIUS = 15
SAVEFREQ = 50

default = {
    "alpha": DIFFUSIONCONSTANT, 
    "density":DENSITY, 
    "heatcapacity":HEATCAPACITY, 
    "effect":EFFECT,
    "move": False,
    "moveradius":8,
    "movespeed": 2,
    "radius": LASERRADIUS,
    "legend": "tbd",
    "center": CENTER,
    "calfunc": None,
    "sizestep": SIZESTEP,
    "timestep": TIMESTEP,
}


def loadmesh():
    return [[0 for _ in range(SIZE[0])] for _ in range(SIZE[1])]


def get(op, name, globs):
    if name in op.keys():
        return op[name]
    return globs.get(name, default[name])


def testCorrectionFunctionWithHeatSource(t=10):
    plot = kaxe.Plot()

    # basis
    # mesh = loadMesh('800000-200,0.asc')

    mesh = loadmesh()
    model = HeatEquationModel(mesh, timeStep=TIMESTEP, sizeStep=SIZESTEP, diffusionConstant=DIFFUSIONCONSTANT)
    model.setSaveSettings(folderNamePath='res', saveFreq=SAVEFREQ, relativeScale=True, toImage=False)

    source = HeatSource(model, effect=EFFECT, heatCapacity=HEATCAPACITY, density=DENSITY)
    source.circle(CENTER, LASERRADIUS)
    source.run()

    model.runUntilTime(t)

    x0 = []
    y0 = []

    for i in getSortedFolder('res/*.asc'):
        data = loadASCII(i)
        simTemp = sum([sum(i) for i in data["map"]]) / (len(data["map"]) * len(data["map"][0]))
        time = data["time"]
        x0.append(time)
        y0.append(simTemp)
    
    p0 = kaxe.Points(x0, y0, connect=True).legend('Uden korrektion')

    # with correction
    mesh = loadmesh()
    model = HeatEquationModel(mesh, timeStep=TIMESTEP, sizeStep=SIZESTEP, diffusionConstant=DIFFUSIONCONSTANT)
    model.setSaveSettings(folderNamePath='res', saveFreq=SAVEFREQ, relativeScale=True, toImage=False)

    source = HeatSource(model, effect=EFFECT, heatCapacity=HEATCAPACITY, density=DENSITY)
    source.circle(CENTER, LASERRADIUS)
    source.run()

    fnc = lambda t, *o: (t * EFFECT) / (HEATCAPACITY * DENSITY * (SIZESTEP * SIZE[0]) * (SIZESTEP * SIZE[1]))
    model.addCorectionFunction(fnc)
    model.runUntilTime(t)

    y1 = []
    x1 = []

    for i in getSortedFolder('res/*.asc'):
        data = loadASCII(i)
        simTemp = sum([sum(i) for i in data["map"]]) / (len(data["map"]) * len(data["map"][0]))
        time = data["time"]
        x1.append(time)
        y1.append(simTemp)

    p1 = kaxe.Points(x1, y1, connect=True).legend('Med korrektion')

    func = kaxe.Function(fnc).legend('Teoretisk')

    plot.add(p0)
    plot.add(p1)
    plot.add(func)
    plot.title(first='Tid', second="Gnm. temperatur")
    plot.save('correction-with-heat.png')


def testParameter(timeend:int, titles:list, fname:str, options:list, globs:dict={}) -> None:
    plot = kaxe.Plot()
    plot.style(windowWidth=2000, windowHeight=2000, fontSize=75)
    plot.title(*titles)

    for op in options:
        mesh = loadmesh()

        model = HeatEquationModel(mesh, timeStep=get(op, "timestep", globs), sizeStep=get(op, "sizestep", globs), diffusionConstant=get(op, "alpha", globs))
        model.setSaveSettings(folderNamePath='res', saveFreq=SAVEFREQ, relativeScale=True, toImage=False)

        source = HeatSource(model, effect=get(op, 'effect', globs), heatCapacity=get(op, 'heatcapacity', globs), density=get(op, 'density', globs))
        source.circle(get(op, 'center', globs), get(op, "radius", globs))
        
        if get(op, 'move', globs):
            radius = get(op, 'moveradius', globs)
            speed = get(op, 'movespeed', globs)
            source.move(lambda t, *_: (math.cos(t*speed)*radius, math.sin(t*speed)*radius))
        
        source.run()

        calfunc = get(op, 'calfunc', globs)
        if calfunc:
            model.addCorectionFunction(calfunc)
        
        model.runUntilTime(timeend)

        x0 = []
        y0 = []

        for i in getSortedFolder('res/*.asc'):
            data = loadASCII(i)
            simTemp = max([np.average(row) for row in data["map"]]) - min([np.average(row) for row in data["map"]])
            time = data["time"]
            x0.append(time)
            y0.append(simTemp)
        
        p = kaxe.Points(x0, y0, connect=True).legend(get(op,'legend', globs))
        plot.add(p)
    
    plot.save(fname)


def main():
    liveViewer(SIZE, 'res', True)
    basiscalfunc = lambda t, *o: (t * EFFECT) / (HEATCAPACITY * DENSITY * (SIZESTEP * SIZE[0]) * (SIZESTEP * SIZE[1]))
    
    t = 50

    # uden bevægelse
    # effect
    if not True:
        testParameter(t, ["Tid efter start",'max(T) - min(T)'], 'parav2/effect.png', [
            {"effect": 25, "legend":"25W"},
            {"effect": 50, "legend":"50W"},
            {"effect": 100, "legend":"100W"},
            {"effect": 250, "legend":"250W"},
            {"effect": 500, "legend":"500W"},
        ], )

    # diffusion constant + density
    if not True:
        testParameter(t, ["Tid efter start",'max(T) - min(T)'], 'parav2/materialer.png', [
            {
                "legend": "Stål", 
                "calfunc": lambda t, *o: (t * EFFECT) / (HEATCAPACITY * DENSITY * (SIZESTEP * SIZE[0]) * (SIZESTEP * SIZE[1]))
            },
            {
                "legend": "Duplex",
                "alpha": 4.039023178*10**(-6),
                "density": 7.7,
                "heatcapacity": 418,
                "calfunc": lambda t, *o: (t * EFFECT) / (418 * 7.7 * (SIZESTEP * SIZE[0]) * (SIZESTEP * SIZE[1]))
            },
            {
                "legend": "Aluminium",
                "alpha": 6.4*10**(-5),
                "density": 2.67,
                "heatcapacity": 896,
                "calfunc": lambda t, *o: (t * EFFECT) / (896 * 2.67 * (SIZESTEP * SIZE[0]) * (SIZESTEP * SIZE[1]))
            }, # https://matweb.com/search/DataSheet.aspx?MatGUID=b8d536e0b9b54bd7b69e4124d8f1d20a
            { #done
                "legend": "Messing",
                "alpha": 3.436018957*10**(-5), #116 W/m-K
                "density": 8.44,
                "heatcapacity": 400,
                "calfunc": lambda t, *o: (t * EFFECT) / (400 * 8.44 * (SIZESTEP * SIZE[0]) * (SIZESTEP * SIZE[1]))
            },
        ])
    

    # radius
    if not True:
        testParameter(t, ["Tid efter start",'max(T) - min(T)'], 'parav2/radius.png', [
            {"radius": 1,"legend": str(round(1 * SIZESTEP*1000, 5))+'mm'},
            {"radius": 2, "legend": str(round(2 * SIZESTEP*1000, 5))+'mm'},
            {"radius": 5,"legend": str(round(5 * SIZESTEP*1000, 5))+'mm'},
            {"radius": 7,"legend": str(round(7 * SIZESTEP*1000, 5))+'mm'},
            {"radius": 10,"legend": str(round(10 * SIZESTEP*1000, 5))+'mm'},
        ], {"calfunc": basiscalfunc})
    
    # med bevægelse
    # radius
    if not True:
        testParameter(t, ["Tid efter start",'max(T) - min(T)'], 'parav2/move-radius.png', [
            {"moveradius": 0,"legend": str(round(0 * SIZESTEP*1000, 5))+'mm'},
            {"moveradius": 2.5, "legend": str(round(2.5 * SIZESTEP*1000, 5))+'mm'},
            {"moveradius": 5,"legend": str(round(5 * SIZESTEP*1000, 5))+'mm'},
            {"moveradius": 10,"legend": str(round(10 * SIZESTEP*1000, 5))+'mm'},
            {"moveradius": 12.5,"legend": str(round(12.5 * SIZESTEP*1000, 5))+'mm'},
        ], {"move": True})
    
    # speed
    if True:
        testParameter(25, ["Tid efter start",'max(T) - min(T)'], 'parav2/move-speed.png', [
            {"movespeed": 1,"legend": str(round(1 * SIZESTEP*1000, 5))+' 1/s'},
            {"movespeed": 2,"legend": str(round(2 * SIZESTEP*1000, 5))+' 1/s'},
            {"movespeed": 5,"legend": str(round(5 * SIZESTEP*1000, 5))+' 1/s'},
            {"movespeed": 10,"legend": str(round(10 * SIZESTEP*1000, 5))+' 1/s'},
            {"movespeed": 20,"legend": str(round(20 * SIZESTEP*1000, 5))+' 1/s'},
        ], {"move": True, "radius":5})

    closeLiveViewer()


if __name__ == '__main__':
    main()