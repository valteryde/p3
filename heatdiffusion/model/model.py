
# Heat diffusion
# Transient Heat equation devolped by Joseph Fourier
# with Adiabatic boundary conditions on all sides
# Modeld with use of FDM (Finite diffrence method)

import math
from .parser import convertFramesToImages, makeVideo, convertFramesToASCII
from .draw import drawCircle, drawRectangle, drawDonut
from tqdm import tqdm
import time
import os
import glob
import sys
import numpy as np


class HeatEquationModel:

    def __init__(self, mesh, timeStep=0.1, sizeStep=0.001, diffusionConstant=0.23*10**(-4)) -> None:
        """
        UNITS:METRIC:

            mass: [kg]
            time: [s]
            length: [m]
        """

        self.hmap = {}
        self.mesh = mesh
        self.heapSize = 10
        self.saveRelativeScale = True
        self.saveAsImage = False
        self.correctionFunction = None
        self.convection = None
        
        self.rules = {}
        self.globalRules = []

        self.lengths = [len(self.mesh[0])-1,len(self.mesh)-1]
        self.len = [self.lengths[0]+1,self.lengths[1]+1]

        #F__0 = alpha*`&Delta;t`/`&Delta;x`^2
        self.timeStep = timeStep #s
        self.sizeStep = sizeStep #m
        self.F0 = (diffusionConstant * self.timeStep) / (self.sizeStep**2)
        # F0 < 1/2

        # add initial data to hmap
        for j, row in enumerate(self.mesh):
            
            for i, T in enumerate(row):

                self.hmap[i, j, 0] = T

        self.saveFolderName = None
        self.saveFreq = 0
        self.correctionMap = None


    def setSaveSettings(self, folderNamePath, saveFreq, relativeScale:bool=False, toImage=False):
        self.saveFolderName = folderNamePath
        self.saveRelativeScale = relativeScale
        self.saveAsImage = toImage

        self.saveFreq = saveFreq
        files = glob.glob('{}/*.png'.format(folderNamePath)) + glob.glob('{}/*.asc'.format(folderNamePath))
        for f in files:
            os.remove(f)


    def __trimHashMap__(self, ns):
        """
        para: (
            n : n'th will be spared
        )
        """

        for i,j,n in list(self.hmap.keys()):

            if n >= ns:
                continue

            del self.hmap[i,j,n]


    def __extractFramesInHeap__(self, heap):
        if self.saveFreq == 0: return
        if not self.saveFolderName: return

        frames = []
        names = []
        for i in range(self.heapSize*(heap-1),self.heapSize*heap):
            if i % self.saveFreq != 0:
                continue

            frames.append(self.__extractFrame__(i))
            names.append(str(i)+'-'+str(i*self.timeStep))

        if self.saveAsImage:
            convertFramesToImages(frames, names, self.saveRelativeScale)
        else:
            convertFramesToASCII(frames, names)


    def __extractFrame__(self, n):
        
        frame = []

        for i in range(self.len[0]):
            frame.append([])
            for j in range(self.len[1]):
                
                try:
                    frame[-1].append(self.hmap[i,j,n])
                except KeyError:
                    print((i,j,n), 'could not be found')
                    frame[-1].append(0)
        
        return frame


    def __correct__(self, heap, t):
        if not self.correctionFunction: return

        surroundingTemperature = 0
        currentTemp = sum([sum([self.hmap[i,j,heap] for j in range(self.len[1])]) for i in range(self.len[0])])
        currentTempAvg = currentTemp / (self.len[0] * self.len[1])

        # if surroundingTemperature >= currentTempAvg:
        #     return

        totalNodes = (self.len[0]) * (self.len[1])
        heatloss = {}
        heatlossSum = 0

        for i in range(self.len[0]):
            for j in range(self.len[1]):
                
                if surroundingTemperature > self.hmap[i,j,heap]:
                    heatloss[i,j] = 0
                    continue

                diff = self.hmap[i,j,heap] - surroundingTemperature
                # if diff < 0: diff = 0
                heatloss[i,j] = diff
                heatlossSum += diff

        #if -1500 < heatlossSum < 1500: return # jeg har ingen ide hvorfor det her virker... pls ik slet 
        correctTemp = self.correctionFunction(t, None) * totalNodes

        gamma = (currentTemp - correctTemp) / heatlossSum

        # if gamma < 0.5:
        #     return
        # if abs(heatlossSum) < 1000:
        #     return
        #print(gamma, correctTemp/totalNodes, currentTemp/totalNodes, correctTemp - currentTemp, tspoida, heatlossSum)
        
        # update
        for i in range(self.len[0]):
            for j in range(self.len[1]):
                self.hmap[i,j,heap] -= heatloss[i,j] * gamma


    # *** API ***
    def addRule(self, node, f):
        self.rules[node[0], node[1]] = f


    def addGlobalRule(self, f, expire=math.inf):
        self.globalRules.append([f, expire])

    def addCorectionFunction(self, func:callable):
        #korrigerings funktion
        self.correctionFunction = func


    def addConvection(self, h, density, heatcapacity, Tsurr=20):
        """
        h / (heatcapacity * density*sizestep*sizestep), Tsurr
        deltaT = h*A*(T - T__omg)*t/(m*c)
        htemp = h/(m*c)
        """
        htemp = h / (heatcapacity * density*self.sizeStep*self.sizeStep)
        self.convection = (
            htemp*(self.sizeStep**2)*self.timeStep,
            Tsurr
        )


    def run(self, breakFuntion=lambda *args: False) -> None:
        """
        para: (
            t time,
            save int if 0 only last frame is saved else every %
        )

        alg:
            to keep hmap size low, we do the model in heaps of 10 iterations.
        """

        startTime = time.time()
        
        # totalTimes = math.ceil(t / self.timeStep)
        # totalHeaps = math.ceil(totalTimes / self.heapSize)
        
        currentHeap = 0

        tempDiffrenceData = []
        error = False

        try:
            while True:
                currentHeap += 1

                timeElapsed = currentHeap*self.heapSize*self.timeStep
                heap = currentHeap * self.heapSize
                minTemp = math.inf
                maxTemp = -math.inf

                for j, row in enumerate(self.mesh):
                    
                    for i, _ in enumerate(row):
                        
                        T = self.T(i, j, heap)
                        minTemp = min(minTemp, T)
                        maxTemp = max(maxTemp, T)
                
                # correction
                self.__correct__(heap, timeElapsed)

                tempDiffrence = maxTemp - minTemp
                tempDiffrenceData.append((timeElapsed,tempDiffrence))

                self.__extractFramesInHeap__(currentHeap)
                self.__trimHashMap__(heap)
                
                if breakFuntion(timeElapsed, tempDiffrence, minTemp, maxTemp, heap): break

        except ImportError: #---
            error = True
            type, value, traceback = sys.exc_info()
            print('[Error]')
            print(type, value, traceback)
        
        finaleFrame = self.__extractFrame__(heap)
        
        if self.saveAsImage:
            convertFramesToImages([finaleFrame], [str(heap)+'-'+str(timeElapsed)], relativeTempScale=self.saveRelativeScale)
        else:
            convertFramesToASCII([finaleFrame], [str(heap)+'-'+str(timeElapsed)])

        return {
            "timeTaken" : round(time.time() - startTime, 2),
            "endTime": timeElapsed,
            "tempDiffrences":tempDiffrenceData,
            "finaleFrame" : finaleFrame,
            "finaleTemperatur": (minTemp, maxTemp),
            "error": error
        }


    def runUntilTime(self, endTime):
        
        bar = tqdm(total=math.ceil(endTime/self.timeStep))

        def end(t, *o):
            
            bar.update(n=self.heapSize)

            if t >= endTime:
                return True

        res = self.run(end)
        bar.close()
        return res


    def runUntilIteration(self, endIteration):
        
        bar = tqdm(total=endIteration)

        def end(t, _1, _2, _3, iteration):
            
            bar.update(n=self.heapSize)

            if iteration >= endIteration:
                return True

        res = self.run(end)
        bar.close()
        return res


    def runUntilUniform(self, dT, numbTime=0):
        """
        para: (
            d: diffrence within body
        )
        """

        def end(t, dT_, minT, maxT):
            print('[INFO] Temperature diffrence:',round(dT_, 5) , 't =', round(t, 5), end="\r", flush=True)
            
            if dT_ <= dT and numbTime <= t:
                return True 

        return self.run(end)

        #self.T(0, 0, totalTimes)


    # *** MODEL ***
    def T(self, i, j, n): # temperature function
        # "distributer" function
        # "hub" function

        if (i,j,n) in self.hmap:
            return self.hmap[i,j,n]

        T = None

        # CORNES
        
        # left top
        if i == 0 and j == 0:
            T = self.corner(i, j, n, (1, 0), (0, 1))

        # right top
        elif i == self.lengths[0] and j == 0:
            T = self.corner(i, j, n, (self.lengths[0]-1, j), (i, 1))
        
        # right bottom
        elif i == self.lengths[0] and j == self.lengths[1]:
            T = self.corner(i, j, n, (self.lengths[0]-1, j), (i, self.lengths[1]-1))

        # left bottom
        elif i == 0 and j == self.lengths[1]:
            T = self.corner(i, j, n, (1, j), (i, self.lengths[1]-1))

        # SIDES
        elif i == 0:
            T = self.side(i, j, n, (i, j+1), (i+1, j), (i, j-1))
        
        elif i == self.lengths[0]:
            T = self.side(i, j, n, (i, j+1), (i-1, j), (i, j-1))

        elif j == 0:
            T = self.side(i, j, n, (i+1, j), (i, j+1), (i-1, j))
        
        elif j == self.lengths[1]:
            T = self.side(i, j, n, (i+1, j), (i, j-1), (i-1, j))

        else:
            T = self.center(i, j, n)

        # External heat
        # meeeega langsomt
        for ruleNum, (rule, expire) in enumerate(self.globalRules):
            if n*self.timeStep > expire:
                self.globalRules.pop(ruleNum)
                break

            T = rule(i, j, T, n, n*self.timeStep, self.timeStep)

        if self.rules.get((i,j)): #kan kun sætte en regel på hver, brug sets for ikkke at have dobbels.
            T = self.rules[i,j](T, n, n*self.timeStep, self.timeStep)

        if self.convection:
            T -= self.convection[0] * (T - self.convection[1])

        self.hmap[i,j,n] = T

        return T


    # cases
    def center(self, i, j, n):
        #T[i + 1, j]^n + T[i - 1, j]^n + T[i, j + 1]^n + T[i, j - 1]^n - (4 - 1/F__0)*T[i, j]^n = T[i, j]^(n + 1)/F__0;

        return self.F0 * (self.T(i+1, j, n-1) + self.T(i - 1, j, n-1) + self.T(i, j+1, n-1) + self.T(i, j-1, n-1) - self.T(i, j, n-1) * (4 - 1/self.F0)) #tror der er i slut gør modellen upræcis


    def corner(self, i, j, n, hn:tuple, vn:tuple):
        
        #[T[1]^n + T[3]^n + (1/(2*F__0) - 2)*T[0]^n]*2*F_0 = T[0]^(n + 1)

        # 1 is vertical neighbour (vn)
        # 3 is horizontal neighbour (hn)

        # return ( self.T(*vn, n-1) + self.T(*hn, n-1) + self.T(i, j, n-1) * (1 / (2 * self.F0 ) - 2) ) * 2 * self.F0
        return ( self.T(*vn, n-1) + self.T(*hn, n-1) + self.T(i, j, n-1) * (1 / self.F0 - 2) ) * self.F0


    # sides
    def side(self, i, j, n:int, n0:tuple, n2:tuple, n4:tuple):

        """
        para: (
            n: timeframe
            n0, n2, n4: neighbours
        )
        """

        #[2*T[2]^n + T[4]^n + T[0]^n - (4 - 1/F__0)*T[1]^n]*F__0 = T[1]^(n + 1)
        #NOTE: jeg her ændret 2 til 1 her
        # return self.F0 * ( 2 * self.T(*n2, n-1) + self.T(*n0, n-1) + self.T(*n4, n-1) + (1/self.F0 - 4) * self.T(i, j, n-1) )
        return self.F0 * ( self.T(*n2, n-1) + self.T(*n0, n-1) + self.T(*n4, n-1) + (1/self.F0 - 3) * self.T(i, j, n-1) )
