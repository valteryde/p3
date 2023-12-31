
# callibrate.py
import os
import glob
from kaxe import plot, objects, regression
from kaxe.data import loadExcel
import numpy as np
from PIL import Image
import math
from .apply import createCalFunction, callibrateExcel

def rsquared(lx, ly, f):
    #https://en.wikipedia.org/wiki/Coefficient_of_determination
    yavg = np.average(ly)
    SST = sum([(y - yavg)**2 for y in ly])
    SSReg = sum([(ly[i] - f(x))**2 for i, x in enumerate(lx)])
    return 1 - SSReg/SST


def showImage(path):
    print('Laver graf (vent venligst)')
    xlsx = glob.glob(os.path.join(path, 'temperature', '*.xlsx'))

    data = []
    for file in xlsx:
        data.extend(loadExcel(file, 'Sheet', (1,1), (4,-1)))

    inner = [(i[1],i[2]) for i in data]
    outer = [(i[3],i[0]) for i in data]
    #data = [*inner, *outer]

    # pl = plot.Plot([0,400,0,500])
    pl = plot.Plot()
    pl.title(first='Blank overflade', second='Malet overflade')

    x0 = [i[0] for i in inner]
    y0 = [i[1] for i in inner]
    p0 = objects.Points(x0,y0, size=15).legend('Indre')
    pl.add(p0)

    x1 = [i[0] for i in outer]
    y1 = [i[1] for i in outer]
    p1 = objects.Points(x1,y1, size=15).legend('Ydre')
    pl.add(p1)

    #minmaxy = [y[i] for i in range(len(y))]

    #pl.add(objects.Function(lambda x, a: a, a=max(minmaxy)).legend('Max: {}'.format(max(minmaxy))))
    #pl.add(objects.Function(lambda x, a: a, a=min(minmaxy)).legend('Min: {}'.format(min(minmaxy))))

    pl.save('.__prereg.png')
    im = Image.open('.__prereg.png')
    #os.remove('.__prereg.png')
    im.show()
    im.close()
    return '.__prereg.png'


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

    #bordervalues.insert(0, min(data, key=lambda d: d[0])[0])
    #bordervalues.append(max(data, key=lambda d: d[0])[0])
    bordervalues.insert(0, -math.inf)
    bordervalues.append(math.inf)

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


def compareCallibratedExcel(path, calfuncname):
    interval = [None, None]
    
    if input('Ændre grænser? [Y/N]:').lower() == 'y':
        a = int(input('Nedre grænse:'))
        b = int(input('Øvre grænse:'))
        interval = [a,b]

    print('Henter data')
    plt = plot.Plot([None, None, *interval])
    plt.style(windowHeight=3000,windowWidth=3000,fontSize=60)
    plt.title(first='Kalibreret blank overflade', second='Malet overflade')

    xlsx = glob.glob(os.path.join(path, 'temperature', '*.xlsx'))
    data = []
    for file in xlsx:
        data.extend(loadExcel(file, 'Sheet', (1,1), (4,-1)))

    data = [i for i in data if not any(map(lambda x: x is None, i))]
    
    if len(data) == 0:
        print('[ERROR] Ingen data')
        return 

    # calibrated
    cxlsx = glob.glob(os.path.join(path, 'calibrated', '*.xlsx'))
    cdata = []
    for file in cxlsx:
        cdata.extend(loadExcel(file, 'Sheet', (1,1), (4,-1)))

    cdata = [i for i in cdata if not any(map(lambda x: x is None, i))]

    if len(cdata) == 0:
        print('[ERROR] Ingen data')
        return 

    # x,y
    ax = [cdata[i][3] for i in range(len(data))]
    ay = [data[i][0] for i in range(len(data))]
    
    bx = [cdata[i][1] for i in range(len(data))]
    by = [data[i][2] for i in range(len(data))]
    
    x = [*ax, *bx]
    y = [*ay, *by]

    y = [y[i] for i in range(len(y))]

    #if interval[0] and interval[1]:
    #    minmaxy = [i for i in y if interval[0] < i < interval[1]]
    #else:
    #    minmaxy = y

    #funcmax = objects.Function(lambda x, a: a, a=max(minmaxy)).legend('Max: {}'.format(max(minmaxy)))
    #funcmin = objects.Function(lambda x, a: a, a=min(minmaxy)).legend('Min: {}'.format(min(minmaxy)))
    
    # plt.add(funcmax)
    # plt.add(funcmin)

    # plot
    reg = regression(lambda x,a,b: a*x+b, x,y)
    a,b = reg[0]

    func = objects.Function(lambda x,a,b: a*x+b, a=a, b=b).legend('Reg: a={}, b={}, r^2={}'.format(a,b,rsquared(x,y,lambda x: a*x+b)))
    points = objects.Points(x,y, size=15)

    plt.add(points)
    plt.add(func)

    outputfile = os.path.join(path, calfuncname.replace('-res','') +'-compare-'+os.path.split(path)[-1].replace('-res','')+'.png')
    plt.save(outputfile)
    im = Image.open(outputfile)
    im.show()
    im.close()
    print('Output:', outputfile)


def callibrateExcelAndShow(folder, calfile):
    callibrateExcel(folder, calfile)
    compareCallibratedExcel(folder, calfile.split(os.path.sep)[-2])
