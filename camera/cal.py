
# callibrate.py
import os
import glob
from kaxe import plot, objects, regression
from kaxe.data import loadExcel
import numpy as np
from PIL import Image
import math

def showImage(path):
    xlsx = glob.glob(os.path.join(path, '*.xlsx'))

    data = []
    for file in xlsx:
        data.extend(loadExcel(file, 'Sheet', (1,1), (4,-1)))

    inner = [(i[2],i[1]) for i in data]
    outer = [(i[0],i[3]) for i in data]
    data = [*inner, *outer]

    pl = plot.Plot()
    pl.title(second='Blank overflade', first='Malet overflade')
    
    x = [i[0] for i in data]
    y = [i[1] for i in data]
    p = objects.Points(x,y, size=15).legend('Målt')
    pl.add(p)

    pl.save('.__prereg.png')
    im = Image.open('.__prereg.png')
    #os.remove('.__prereg.png')
    im.show()
    im.close()


def createRegression(path):
    
    print('\033[96m'+'Vælg grænseværdier [Skriv et bogstav for at færdiggøre + Tryk enter]'+'\033[0m')
    bordervalues = [-math.inf]
    while True:
        
        inp = input('Grænseværdi: ')

        try:
            bordervalues.append(int(inp))
        except ValueError:
            break

    bordervalues.sort()

    print('Vent venligst (forstil venligt elevatormusik)')

    xlsx = glob.glob(os.path.join(path, '*.xlsx'))

    data = []
    for file in xlsx:
        data.extend(loadExcel(file, 'Sheet', (1,1), (4,-1)))

    plt = plot.Plot()
    plt.title(second='Blank overflade', first='Malet overflade')
    
    inner = [(i[2],i[1]) for i in data if all(map(lambda x: x is None, i))]
    outer = [(i[0],i[3]) for i in data if all(map(lambda x: x is None, i))] #burde tjekke for dårlige pixels
    data = [*inner, *outer]

    funcs = []
    points = []
    for borderindex in range(1,len(bordervalues)):
        
        dx = [x for x,y in data if bordervalues[borderindex-1] < x < bordervalues[borderindex]]
        dy = [y for x,y in data if bordervalues[borderindex-1] < x < bordervalues[borderindex]]

        try:
            reg = regression(lambda x,a,b: a*x+b, dx, dy)
        except ValueError:
            continue
        a,b = reg[0][0], reg[0][1]
        print(']{}, {}], f(x)={}*x +{}'.format(bordervalues[borderindex-1], bordervalues[borderindex], reg[0][0], reg[0][1]))
        
        def func(x, a, b, interval):
            if interval[0] <= x <= interval[1]:
                return a*x+b

        linreg = objects.Function(func, a=a, b=b, interval=[bordervalues[borderindex-1],  bordervalues[borderindex]]).legend('Reg: y={}x+{}'.format(round(a,4),round(b,2)))
        funcs.append(linreg)

        p = objects.Points(dx,dy, size=15).legend('Målt')
        points.append(p)

    for i in points:
        plt.add(i)
    for i in funcs:
        plt.add(i)

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