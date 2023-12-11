
# heat source

import math

class HeatSource:
    
    def __init__(self, model, effect:float, heatCapacity:float, density:int):
        """
        effect [W]
        heatCapacity [J/(kg*C)]
        density [kg/m^2]
        """

        """
        eventuelt gem en liste med de noder der berøres af varmen
        så bare kør over den for hver iteration
        det kan også være mere sikkert at tilsætte energi efterfølgende og ikke løbende.
        """

        self.model = model
        self.effect = effect
        self.heatCapacity = heatCapacity #J/(kg*C)
        self.density = density
        
        self.areaPerPixel = self.model.sizeStep ** 2
        self.massPerPixel = self.areaPerPixel * self.density

        self.meshMass = sum([len(row) for row in self.model.mesh]) * self.massPerPixel


    # shapes
    def donut(self, center, innerRadius, outerRadius):
        """
        center and radius corrosponding to mesh sizes
        """
        
        # not precise
        self.totalPixelsInShape = math.floor(math.pi * ((outerRadius)**2 - (innerRadius)**2))
        self.effectPerPixel = self.effect / self.totalPixelsInShape
        self.deltaEnergyPerPixel = self.effectPerPixel * self.model.timeStep
        self.deltaTemperaturePerPixel = self.deltaEnergyPerPixel / (self.heatCapacity * self.massPerPixel)

        def rule(i, j, T, n, t, dt):

            d = math.sqrt((center[0]-i)**2+(center[1]-j)**2)

            if innerRadius < d < outerRadius:
                return T + self.deltaTemperaturePerPixel
                
            return T

        self.rule = rule
    
    
    def circle(self, center, radius):
        """
        center and radius corrosponding to mesh sizes
        """

        height = len(self.model.mesh)
        width = len(self.model.mesh[0])

        pixels = {}
        sumIntensity = 0

        sigma = (radius / 2)

        for i in range(-int(radius)*2,width+int(radius)*2):

            for j in range(-int(radius)*2, height+int(radius)*2):

                d = math.sqrt((center[0]-i)**2+(center[1]-j)**2)
                val = 1/(math.sqrt(2 * math.pi * sigma**2))*math.exp((-d**2)/(2*sigma**2))
                sumIntensity += val
                    
                if (0 <= i <= width) and (0 <= j <= height):
                    pixels[i,j] = val

        self.deltaEnergy = self.effect * self.model.timeStep
        self.deltaTemperature = self.deltaEnergy / (self.heatCapacity * self.massPerPixel)

        for key in pixels:

            pixels[key] = (pixels[key] / sumIntensity) * self.deltaTemperature

        s = 0
        for key in pixels:
            s += pixels[key]
        print('\033[93mDer tilføjes {} grader hver frame ud af {} tilgængelige grader ({}%)\033[0m'.format(self.model.sizeStep**2 * s, self.model.sizeStep**2 * s, s/self.deltaTemperature*100))

        def rule(i, j, T, n, t, dt):

            #d = math.sqrt((center[0]-i)**2+(center[1]-j)**2)

            return T + pixels.get((i,j), 0)

        self.rule = rule


    def move(self, pattern: callable):
        
        self.__rule__ = self.rule

        def rule(i, j, T, n, t, dt):
            oi, oj = pattern(t)
            oi, oj = int(oi), int(oj)

            i -= oi
            j -= oj
            if not (0 < i < self.model.len[0]) or not (0 < j < self.model.len[1]):
                return T

            return self.__rule__(i,j, T, n, t, dt)

        self.rule = rule


    # def rectangle(self):
    #     pass

    # goal
    def goal(self, dT):
        self.totalTimeActive = (self.heatCapacity * dT * self.meshMass) / self.effect
        self.model.addGlobalRule(self.rule, expire=self.totalTimeActive)
    

    def run(self, t=math.inf):
        self.model.addGlobalRule(self.rule, expire=t)
