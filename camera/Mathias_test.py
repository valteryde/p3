import os
import glob
from kaxe import plot, objects, regression
from kaxe.data import loadExcel
import numpy as np
from PIL import Image
import math
from .apply import createCalFunction, callibrateExcel
from interface import selectionWindow, displayData
from interface import selectWrapper as wrapper
import platform
from .process import analyzeFromFolder
from .cal import createRegression
from kaxe import resetColor


REGRESSIONSNAMES = ["Lineær", "2. poly", "3. poly", "4. poly", "5. poly"]
REGRESSIONS = [
    (lambda x,a,b: a*x+b,  "{}*x+{}"),
    (lambda x,a,b,c: a*x**2+b*x+c, "{}*x**2+{}*x+{}"),
    (lambda x,a,b,c,d: a*x**3+b*x**2+c*x+d, "{}*x**3+{}*x**2+{}*x+{}"),
    (lambda x,a,b,c,d,e: a*x**4+b*x**3+c*x**2+d*x+e, "{}*x**4+{}*x**3+{}*x**2+{}*x+{}"),
    (lambda x,a,b,c,d,e,f: a*x**5+b*x**4+c*x**3+d*x**2+e*x+f, "{}*x**5+{}*x**4+{}*x**3+{}*x**2+{}*x+{}")
]

def rsquared(lx, ly, f):
    #https://en.wikipedia.org/wiki/Coefficient_of_determination
    yavg = np.average(ly)
    SST = sum([(y - yavg)**2 for y in ly])
    SSReg = sum([(ly[i] - f(x))**2 for i, x in enumerate(lx)])
    return 1 - SSReg/SST


def openFilesFolder():
    
    path = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'files')
    
    if platform.system() == 'Darwin':
        os.system('open {}'.format(path))
    elif platform.system() == 'Windows':
        os.system('start files')

def clear():
    os.system('cls||clear')

def showImageMT(path): #regression ligning
    print('Laver graf (vent venligst)')
    xlsx = glob.glob(os.path.join(path, 'temperature', '*.xlsx'))

    data = []
    for file in xlsx:
        data.extend(loadExcel(file, 'Sheet', (1,1), (4,-1)))

    inner = [(i[1],i[2]) for i in data]
    outer = [(i[3],i[0]) for i in data]
    data = [*inner, *outer]

    pl = plot.Plot()
    pl.style(windowHeight=2000,windowWidth=2000,fontSize=60)
    pl.title(first='Blank overflade', second='Malet overflades')

    x = [i[0] for i in data]
    y = [i[1]-i[0] for i in data]
    p = objects.Points(x,y, size=15,color=(242,196,58,255)).legend('Målt')
    pl.add(p)

    #minmaxy = [y[i] for i in range(len(y))]

    #pl.add(objects.Function(lambda x, a: a, a=max(minmaxy)).legend('Max: {}'.format(round(max(minmaxy),3))))
    #pl.add(objects.Function(lambda x, a: a, a=min(minmaxy)).legend('Min: {}'.format(round(min(minmaxy),3))))

    outputfile = os.path.join(path, os.path.split(path)[-1])
    pl.save(outputfile)
    #im = Image.open('.__prereg.png')
    #os.remove('.__prereg.png')
    #im.show()
    #im.close()


def starLineExpressMT(path): #kaliberings graf
    basepath = 'files'
    files = os.listdir(basepath)

    files = [i for i in files if i not in [".DS_Store", 'config.json'] and '.' not in i and i[-4:] not in ['-res', '-cal']]
    choice = selectionWindow('Vælg mappe',["<-- Gå tilbage", "[Klik her for at åbne mappe]"] + files)

    if choice[0] == 0: 
        return False
    
    if choice[0] == 1:
        openFilesFolder()
        return False
    
    analyzeFromFolder(os.path.join(basepath,choice[1]), 'files')
    clear()
    print('\033[96m'+'Når denne process er færdig, vil dataen blive vist på en graf. Læg her mærke til hop i HDR. Disse værdier skal bruges efterfølgende'+'\033[0m')
    showImageMT(os.path.join(basepath,choice[1]+'-res'))
    typereg = selectionWindow('Vælg type af regression',REGRESSIONSNAMES)
    resetColor()
    createRegression(os.path.join(basepath,choice[1]+'-res'), *REGRESSIONS[typereg[0]])
    return True

def createRegressionMT(path, regtype=lambda x,a,b: a*x+b, regtypelabel='{}x+{}'):
    
    print('\033[96m'+'Vælg grænseværdier [Skriv et bogstav for at færdiggøre + Tryk enter]'+'\033[0m')
    bordervalues = []
    while True:
        
        inp = input('Grænseværdi: ')

        try:
            bordervalues.append(int(inp))
        except ValueError:
            break

    bordervalues.sort()

    print('Henter data (*elevatormusik*)')

    xlsx = glob.glob(os.path.join(path, 'temperature', '*.xlsx'))

    data = []
    for file in xlsx:
        data.extend(loadExcel(file, 'Sheet', (1,1), (4,-1)))

    plt = plot.Plot()
    plt.title(first='Blank overflade', second='Malet overflade')
    
    inner = [(i[1],i[2]-i[1]) for i in data if not any(map(lambda x: x is None, i))]
    outer = [(i[3],i[0]-i[3]) for i in data if not any(map(lambda x: x is None, i))] #burde tjekke for dårlige pixels
    data = [*inner, *outer]

    bordervalues.insert(0, min(data, key=lambda d: d[0])[0])
    bordervalues.append(max(data, key=lambda d: d[0])[0])

    funcs = []
    points = []
    fs = []
    for borderindex in range(1,len(bordervalues)):
        
        dx = [x for x,y in data if bordervalues[borderindex-1] < x < bordervalues[borderindex]]
        dy = [y for x,y in data if bordervalues[borderindex-1] < x < bordervalues[borderindex]]

        if len(dx) == 0 or len(dy) == 0:
            continue

        try:
            reg = regression(regtype, dx, dy)
        except ImportError:
            continue
        print(']{}, {}] {}'.format(bordervalues[borderindex-1], bordervalues[borderindex], regtypelabel.format(*reg[0])))

        def func(x, regs, interval, fnc):
            if interval[0] <= x <= interval[1]:
                return fnc(x, *regs) # farligt, men tager ikke user input her så det går nok

        freg = objects.Function(func, fnc=regtype, regs=[float(i) for i in reg[0]], interval=[bordervalues[borderindex-1],  bordervalues[borderindex]]).legend(regtypelabel.format(*map(lambda a: round(a, 3), reg[0]))+ ' r^2={}'.format(round(rsquared(dx, dy, lambda x: regtype(x, *reg[0])), 5)))
        funcs.append(freg)
        fs.append(([bordervalues[borderindex-1],  bordervalues[borderindex]], regtypelabel.format(*reg[0])))

        p = objects.Points(dx,dy, size=15).legend('Målt')
        points.append(p)

    for i in points:
        plt.add(i)
    for i in funcs:
        plt.add(i)
    plt.style(windowHeight=2000,windowWidth=2000,fontSize=60)
    createCalFunction(os.path.join(path, 'func.cal'), fs)

    # reg = regression(lambda x,a,b,c: a*np.power(x, 2) + b*x + c, x, y)
    # d, e, f = reg[0][0], reg[0][1], reg[0][2]
    # print('f(x) a={} b={} c={}'.format(d, e, f))
    # polyreg = objects.Function(lambda x: d*x**2 + e*x + f).legend('Reg: y=ax^2+bx+c')
    # plot.add(polyreg)

    outputfile = os.path.join(path, os.path.split(path)[-1].replace('-res','')+'.png')
    plt.save(outputfile)
    im = Image.open(outputfile)
    im.show()
    im.close()
    print('Output:', outputfile)
    print('Output:', os.path.join(path, 'func.cal'))
