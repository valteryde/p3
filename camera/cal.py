
# callibrate.py
import os
import glob
from kaxe import plot, objects, regression
from kaxe.data import loadExcel
import numpy as np
from PIL import Image
import math
from .apply import createCalFunction

def showImage(path):
    print('Laver graf (vent venligst)')
    xlsx = glob.glob(os.path.join(path, 'temperature', '*.xlsx'))

    data = []
    for file in xlsx:
        data.extend(loadExcel(file, 'Sheet', (1,1), (4,-1)))

    inner = [(i[1],i[2]) for i in data]
    outer = [(i[3],i[0]) for i in data]
    data = [*inner, *outer]

    pl = plot.Plot()
    pl.title(first='Blank overflade', second='Malet overflade')
    
    x = [i[0] for i in data]
    y = [i[1] for i in data]
    p = objects.Points(x,y, size=15).legend('Målt')
    pl.add(p)

    pl.save('.__prereg.png')
    im = Image.open('.__prereg.png')
    #os.remove('.__prereg.png')
    im.show()
    im.close()


def createRegression(path, regtype=lambda x,a,b: a*x+b, regtypelabel='{}x+{}'):
    
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
    
    inner = [(i[1],i[2]) for i in data if not any(map(lambda x: x is None, i))]
    outer = [(i[3],i[0]) for i in data if not any(map(lambda x: x is None, i))] #burde tjekke for dårlige pixels
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
        print(']{}, {}]'.format(bordervalues[borderindex-1], bordervalues[borderindex]) + regtypelabel.format(*reg[0]))

        def func(x, regs, interval, fnc):
            if interval[0] <= x <= interval[1]:
                return fnc(x, *regs) # farligt, men tager ikke user input her så det går nok

        freg = objects.Function(func, fnc=regtype, regs=[float(i) for i in reg[0]], interval=[bordervalues[borderindex-1],  bordervalues[borderindex]]).legend(regtypelabel.format(*map(lambda a: round(a, 3), reg[0])))
        funcs.append(freg)
        fs.append(([bordervalues[borderindex-1],  bordervalues[borderindex]], regtypelabel.format(*reg[0])))

        p = objects.Points(dx,dy, size=15).legend('Målt')
        points.append(p)

    for i in points:
        plt.add(i)
    for i in funcs:
        plt.add(i)

    createCalFunction(os.path.join(path, 'func.cal'), fs)

    # reg = regression(lambda x,a,b,c: a*np.power(x, 2) + b*x + c, x, y)
    # d, e, f = reg[0][0], reg[0][1], reg[0][2]
    # print('f(x) a={} b={} c={}'.format(d, e, f))
    # polyreg = objects.Function(lambda x: d*x**2 + e*x + f).legend('Reg: y=ax^2+bx+c')
    # plot.add(polyreg)

    outputfile = os.path.join(path, 'curve.png')
    plt.save(outputfile)
    im = Image.open(outputfile)
    im.show()
    im.close()
    print('Output:', outputfile)
    print('Output:', os.path.join(path, 'func.cal'))