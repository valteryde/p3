
from model import *
import math
import time

EFFECT = 1000
SIZE = (101,101) # width, height
CENTER = (SIZE[0]//2, SIZE[1]//2)

HEATCAPACITY = 500
DENSITY = 8
TIMESTEP = 0.0025
SIZESTEP = 0.001
DIFFUSIONCONSTANT = 4.2*10**(-6)
LASERRADIUS = 35
SAVEFREQ = 100
LASERTIME = 12.5
TIME = 200


def loadmesh():
    return [[0 for _ in range(SIZE[0])] for _ in range(SIZE[1])]


def corrfunc(t, T):
    if t > LASERTIME:
        return (LASERTIME * EFFECT) / (HEATCAPACITY * DENSITY * (SIZESTEP * SIZE[0]) * (SIZESTEP * SIZE[1]))

    return (t * EFFECT) / (HEATCAPACITY * DENSITY * (SIZESTEP * SIZE[0]) * (SIZESTEP * SIZE[1]))


def main():

    # n x n
    mesh = loadmesh()
    # mesh = loadMesh('16000-40,0.asc')

    # model = HeatEquationModel(mesh, timeStep=0.0025, sizeStep=0.002, diffusionConstant=4.075*10**(-6))
    model = HeatEquationModel(mesh, timeStep=TIMESTEP, sizeStep=SIZESTEP, diffusionConstant=DIFFUSIONCONSTANT)
    model.setSaveSettings(folderNamePath='res', saveFreq=SAVEFREQ, relativeScale=False, toImage=True)

    source = HeatSource(model, effect=EFFECT, heatCapacity=HEATCAPACITY, density=DENSITY)
    source.circle(CENTER, LASERRADIUS)
    #source.move(lambda t, *_: (math.cos(t*speed)*radius, math.sin(t*speed)*radius))
    source.run(LASERTIME)

    model.addCorectionFunction(corrfunc)
    model.runUntilTime(TIME)

if __name__ == '__main__':
    # liveViewer(SIZE,'res', ASCII=False)
    main()
    # closeLiveViewer()