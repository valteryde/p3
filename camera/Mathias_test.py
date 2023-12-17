import os
import glob
from kaxe import plot, objects, regression
from kaxe.data import loadExcel 
import numpy as np
from PIL import Image
import math
from .apply import createCalFunction, callibrateExcel, loadCalFunction
from interface import selectionWindow, displayData
from interface import selectWrapper as wrapper
import platform
from .loader import createFolder
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
    print('MT')
    xlsx = glob.glob(os.path.join(path, 'temperature', '*.xlsx'))

    data = []
    for file in xlsx:
        data.extend(loadExcel(file, 'Sheet', (1,1), (4,-1)))

    inner = [(i[1],i[2]-i[1]) for i in data]
    outer = [(i[3],i[0]-i[3]) for i in data]
    data = [*inner, *outer]

    interval = input('ønskes der aksegrænse?[y/n] ')
    if interval == 'y':
        nedre = int(input('nedre grænse: '))
        øvre = int(input('øvre grænse: '))
        pl = plot.Plot([None,None,nedre,øvre])
    else:
        pl = plot.Plot()

    pl.style(windowHeight=2000,windowWidth=2000,fontSize=80)
    pl.title(first='Blank overflade', second='Malet overflades')

    x = [i[0] for i in data]
    y = [i[1] for i in data]
    p = objects.Points(x,y, size=15,color=(242,196,58,255)).legend('Målt')
    pl.add(p)

    #minmaxy = [y[i] for i in range(len(y))]

    #pl.add(objects.Function(lambda x, a: a, a=max(minmaxy)).legend('Max: {}'.format(round(max(minmaxy),3))))
    #pl.add(objects.Function(lambda x, a: a, a=min(minmaxy)).legend('Min: {}'.format(round(min(minmaxy),3))))

    outputfile = os.path.join(path, os.path.split(path)[-1].replace('-res','')+'.png')
    pl.save(outputfile)
    im = Image.open(outputfile)
    #os.remove('.__prereg.png')
    im.show()
    im.close()


def starLineExpressMT(): #kaliberings graf fra ASCII filer
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
    createRegressionMT(os.path.join(basepath,choice[1]+'-res'), *REGRESSIONS[typereg[0]])
    return True

def createRegressionMT(path, regtype=lambda x,a,b: a*x+b, regtypelabel='{}x+{}'): #Kaliberings graf fra aflæst excel fil
    
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

    interval = input('ønskes der aksegrænse?[y/n] ')
    if interval == 'y':
        nedre = int(input('nedre grænse: '))
        øvre = int(input('øvre grænse: '))
        plt = plot.Plot([None,None,nedre,øvre])
    else:
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


def anders_abs_temp_entry(): #kaliberings graf
    basepath = 'files'
    files = os.listdir(basepath)

    files = [i.replace('-res','') for i in files if i not in [".DS_Store", 'config.json'] and '.' not in i and i[-4:] == '-res']
    choice = selectionWindow('Vælg mappe',["<-- Gå tilbage", "[Klik her for at åbne mappe]"] + files)

    if choice[0] == 0: 
        return False
    
    if choice[0] == 1:
        openFilesFolder()
        return False
    
    clear()
    anders_abs_temp_pre(os.path.join(basepath,choice[1]+'-res'))
    anders_abs_temp_post(os.path.join(basepath,choice[1]+'-res'))
    return True


def anders_abs_temp_pre(path):

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
    pl.title(first='Blank overflade', second='Malet overflades afvigelse')

    x0 = [i[0] for i in data]
    y0 = [abs(i[1]-i[0]) for i in data]
    print('Gnm: {}'.format(np.average(y0)))

    #xy = sorted(list(zip(x0,y0)), key=lambda i: i[0])
    stepsize = 5
    mnx = min(x0)
    span = (max(x0)-mnx)
    nx = [[] for _ in range(int(span//stepsize))]
    ny = [[] for _ in range(int(span//stepsize))]
    
    for ix, x in enumerate(x0):

        i = math.floor((x-mnx) / stepsize)-1
        nx[i].append(x)
        ny[i].append(y0[ix])
    
    nxy = [(i[0], i[1]) for i in zip(nx, ny) if i[0] and i[1]]
    nx = [i[0] for i in nxy]
    ny = [i[1] for i in nxy]

    nx = [float(np.average(i)) for i in nx]
    ny = [float(np.average(i)) for i in ny]
    
    #print(nx)
    #print(ny)

    p0 = objects.Points(x0, y0, size=10, color=(242,196,58,255)).legend('Målt')
    p = objects.Points(nx, ny, size=15, color=(0,0,0,255)).legend('Gennemsnit')
    pl.add(p0)
    pl.add(p)

    #minmaxy = [y[i] for i in range(len(y))]

    #pl.add(objects.Function(lambda x, a: a, a=max(minmaxy)).legend('Max: {}'.format(round(max(minmaxy),3))))
    #pl.add(objects.Function(lambda x, a: a, a=min(minmaxy)).legend('Min: {}'.format(round(min(minmaxy),3))))

    outputfile = os.path.join(path, os.path.split(path)[-1]+'-anders_pre.png')
    print(outputfile)
    pl.save(outputfile)
    #im = Image.open('.__prereg.png')
    #os.remove('.__prereg.png')
    #im.show()
    #im.close()


def anders_abs_temp_post(path):
    interval = [None, None]
    
    if input('Hvilket interval ønskes der gennemsnit? [Y/N]: ').lower() == 'y':
        a = int(input('Nedre grænse:'))
        b = int(input('Øvre grænse:'))
        interval = [a,b]


    print('Henter data')
    plt = plot.Plot([None, None, *interval])
    plt.style(windowHeight=2000,windowWidth=2000,fontSize=60)
    plt.title(first='Kalibreret blank overflade', second='Malet overflades afvigelse')

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
    
    x0 = [*ax, *bx]
    y0 = [*ay, *by]

    y0 = [abs(y0[i]-x0[i]) for i in range(len(y0))]

    xy0 = [(i[0], i[1]) for i in zip(x0, y0) if interval[0] <= i[1] <= interval[1]]
    x0 = [i[0] for i in xy0]
    y0 = [i[1] for i in xy0]
    print('Gnm: {}'.format(np.average(y0)))

    print('Laver graf (vent venligst)')
    xlsx = glob.glob(os.path.join(path, 'calibrated', '*.xlsx'))

    data = []
    for file in xlsx:
        data.extend(loadExcel(file, 'Sheet', (1,1), (4,-1)))

    if input('Hvilket interval ønskes der indenfor plottet? [Y/N]: ').lower() == 'y':
        a = int(input('Nedre grænse:'))
        b = int(input('Øvre grænse:'))
        interval = [a,b]

    inner = [(i[1],i[2]) for i in data]
    outer = [(i[3],i[0]) for i in data]
    data = [*inner, *outer]

    pl = plot.Plot([None, None, interval[0], interval[1]])
    pl.style(windowHeight=2000,windowWidth=2000,fontSize=60)
    pl.title(first='Kaliberet blank overflade', second='Malet overflades afvigelse')
    
    #xy = sorted(list(zip(x0,y0)), key=lambda i: i[0])
    stepsize = 5
    mnx = min(x0)
    span = (max(x0)-mnx)
    nx = [[] for _ in range(int(span//stepsize))]
    ny = [[] for _ in range(int(span//stepsize))]
    
    for ix, x in enumerate(x0):

        i = math.floor((x-mnx) / stepsize)-1
        nx[i].append(x)
        ny[i].append(y0[ix])
    
    nxy = [(i[0], i[1]) for i in zip(nx, ny) if i[0] and i[1]]
    nx = [i[0] for i in nxy]
    ny = [i[1] for i in nxy]

    nx = [float(np.average(i)) for i in nx]
    ny = [float(np.average(i)) for i in ny]
    
    #print(nx)
    #print(ny)

    p0 = objects.Points(x0, y0, size=10, color=(242,196,58,255)).legend('Målt')
    p = objects.Points(nx, ny, size=15, color=(0,0,0,255)).legend('Gennemsnit')
    pl.add(p0)
    pl.add(p)

    #minmaxy = [y[i] for i in range(len(y))]

    #pl.add(objects.Function(lambda x, a: a, a=max(minmaxy)).legend('Max: {}'.format(round(max(minmaxy),3))))
    #pl.add(objects.Function(lambda x, a: a, a=min(minmaxy)).legend('Min: {}'.format(round(min(minmaxy),3))))

    outputfile = os.path.join(path, os.path.split(path)[-1]+'-anders_post.png')
    print(outputfile)
    pl.save(outputfile)
    #im = Image.open('.__prereg.png')
    #os.remove('.__prereg.png')
    #im.show()
    #im.close()

def callibrateExcelAndShowMT(folder, calfile):
    compareCallibratedExcelMT(folder, calfile.split(os.path.sep)[-2])

def compareCallibratedExcelMT(path, calfuncname):
    interval = [None, None]
    
    if input('Ændre grænser? [Y/N]:').lower() == 'y':
        a = int(input('Nedre grænse:'))
        b = int(input('Øvre grænse:'))
        interval = [a,b]

    print('Henter data')
    plt = plot.Plot([None, None, *interval])
    plt.style(windowHeight=2000,windowWidth=2000,fontSize=60)
    plt.title(first='Kalibreret blank overflade', second='Malet overflades afvigelse')

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

    y = [y[i]-x[i] for i in range(len(y))]

    if interval[0] and interval[1]:
        minmaxy = [i for i in y if interval[0] < i < interval[1]]
    else:
        minmaxy = y

    funcmax = objects.Function(lambda x, a: a, a=max(minmaxy)).legend('Max: {}'.format(round(max(minmaxy),3)))
    funcmin = objects.Function(lambda x, a: a, a=min(minmaxy)).legend('Min: {}'.format(round(min(minmaxy),3)))
    
    #plt.add(funcmax)
    #plt.add(funcmin)

    # plot
    reg = regression(lambda x,a,b: a*x+b, x,y)
    a,b = reg[0]

   #func = objects.Function(lambda x,a,b: a*x+b, a=a, b=b).legend('Reg: a={}, b={}, r^2={}'.format(a,b,rsquared(x,y,lambda x: a*x+b)))
    points = objects.Points(x,y, size=15,color=(242,196,58,255))

    
    plt.add(points)
    #plt.add(func)

    outputfile = os.path.join(path, calfuncname.replace('-res','') +'-compare-'+os.path.split(path)[-1].replace('-res','')+'.png')
    plt.save(outputfile)
    im = Image.open(outputfile)
    im.show()
    im.close()
    print('Output:', outputfile)


def valter_temp_indre_ydre_graf(path): #regression ligning
    print('Laver graf (vent venligst)')
    xlsx = glob.glob(os.path.join(path, 'temperature', '*.xlsx'))

    data = []
    for file in xlsx:
        data.extend(loadExcel(file, 'Sheet', (1,1), (4,-1)))

    inner = [(i[1],i[2]) for i in data]
    outer = [(i[3],i[0]) for i in data]

    inner = [
        [i[0] for i in inner],
        [i[1] for i in inner],
    ]
    outer = [
        [i[0] for i in outer],
        [i[1] for i in outer],
    ]

    pl = plot.Plot()
    #pl.style(windowHeight=2000,windowWidth=2000,fontSize=60, backgroundColor=(0,0,0,255), markerColor=(255,255,255,255), gridLineColor=(255,255,255,100))
    pl.style(windowHeight=2000,windowWidth=2000,fontSize=60)
    pl.title(first='Blank overflade', second='Malet overflades')

    p0 = objects.Points(inner[0], inner[1], size=15, color=(242,196,58,255)).legend('Indre')
    p1 = objects.Points(outer[0], outer[1], size=15, color=(200,0,58,255)).legend('Ydre')
    pl.add(p0)
    pl.add(p1)

    outputfile = os.path.join(path, os.path.split(path)[-1])
    pl.save(outputfile+'.png')
    #im = Image.open('.__prereg.png')
    #os.remove('.__prereg.png')
    #im.show()
    #im.close()

