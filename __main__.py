
from prepare import setupAndInstall, uninstallPackages
import sys
import os

try:
    from interface import selectionWindow, displayData
    from interface import selectWrapper as wrapper
    from thermocouple import GLOBALVARS, serial_ports, handleCommunication, getNow
    from camera import analyzeFromFolder, createRegression, showImage
    from camera import convertFolder, analyzeFromFolderManual
    from camera import callibrateASCII, callibrateExcel
    from camera import createFolder, callibrateExcelAndShow
    from test import main as test
    from _thread import start_new_thread
    import datetime
    import logging
    import platform
    import math
    import psutil
    from kaxe import resetColor
    # from .install import 
except ImportError:
    print('\033[92mVelkommen!\033[93m Der mangler nogle/en pakke(r)\033[0m')

REGRESSIONSNAMES = ["Lineær", "2. poly", "3. poly", "4. poly", "5. poly"]
REGRESSIONS = [
    (lambda x,a,b: a*x+b,  "{}*x+{}"),
    (lambda x,a,b,c: a*x**2+b*x+c, "{}*x**2+{}*x+{}"),
    (lambda x,a,b,c,d: a*x**3+b*x**2+c*x+d, "{}*x**3+{}*x**2+{}*x+{}"),
    (lambda x,a,b,c,d,e: a*x**4+b*x**3+c*x**2+d*x+e, "{}*x**4+{}*x**3+{}*x**2+{}*x+{}"),
    (lambda x,a,b,c,d,e,f: a*x**5+b*x**4+c*x**3+d*x**2+e*x+f, "{}*x**5+{}*x**4+{}*x**3+{}*x**2+{}*x+{}")
]

def clear():
    os.system('cls||clear')

def printState():
    state = GLOBALVARS["state"].lower()

    if state == 'online':
        return state, 'GREEN'
    
    if state in ['Failed to open', 'offline']:
        return state, 'RED'

    if state == 'starting':
        return state, 'YELLOW'

    return state


def thermocouple():
    ports = serial_ports()
    choice = selectionWindow('Vælg port', ["<-- Gå tilbage"] + ports)

    if choice[0] == 0:
        return

    start_new_thread(handleCommunication, (ports[choice[0]-1],))

    displayData([
        ("Temperatur", lambda: GLOBALVARS["temp"]), 
        ("Status", printState), 
        ("Tidspunkt", lambda: getNow(True, ':')),
        ("Sidst gemt", lambda: GLOBALVARS["last_save"]),
        ("Output", lambda: GLOBALVARS["output_filename"]),
        ("Antal", lambda: str(math.floor(GLOBALVARS['data_points_count']/100)/10)+'k'),
        ("CPU Procent", lambda: str(psutil.cpu_percent())),
        # ("Hukkomelse brugt", lambda: str(psutil.virtual_memory().percent)),
        ("Hukkomelse avalaibale", lambda: str(round(psutil.virtual_memory().available * 100 / psutil.virtual_memory().total, 4))),
        ("Hukkomelse brugt", lambda: str(psutil.Process().memory_info().rss / (1024 * 1024)))
    ])
    # dict(psutil.virtual_memory()._asdict())

def cameraGetTemperatures():
    basepath = 'files'
    files = os.listdir(basepath)

    files = [i for i in files if i not in [".DS_Store", 'config.json'] and '.' not in i and i[-4:] != '-res']

    choice = selectionWindow('Vælg mappe',["<-- Gå tilbage", "[Klik her for at åbne mappe]"] + files)

    if choice[0] == 0: 
        return False
    
    if choice[0] == 1:
        openFilesFolder()
        return False
    
    if '.asc' in choice[1]: #file
        pass
    
    else: #folder
        analyzeFromFolder(os.path.join(basepath,choice[1]), 'files')
        return True


def cameraGetTemperatureManual():
    basepath = 'files'
    files = os.listdir(basepath)

    files = [i for i in files if i not in [".DS_Store", 'config.json'] and '.' not in i and i[-4:] != '-res']

    choice = selectionWindow('Vælg mappe',["<-- Gå tilbage", "[Klik her for at åbne mappe]"] + files)

    if choice[0] == 0: 
        return False
    
    if choice[0] == 1:
        openFilesFolder()
        return False
    
    if '.asc' in choice[1]: #file
        pass
    
    else: #folder
        # t = int(input('Top: '))
        # b = int(input('Bund: '))
        # l = int(input('Venstre: '))
        # r = int(input('Højre: '))
        # t, l, b, r = 116, 97, 325, 498
        clear()
        analyzeFromFolderManual(os.path.join(basepath,choice[1]), 'files')
        return True


def callibrateSecondChoice(choice):
    basepath = 'files'
    files = os.listdir(basepath)
    files = [i for i in files if i not in [".DS_Store", 'config.json'] and '.' not in i and i[-4:] not in ['-res', '-cal']]
    choice2 = selectionWindow('Vælg datasæt',["<-- Gå tilbage", "[Klik her for at åbne mappe]"] + files)

    if choice2[0] == 0: 
        return False
    
    if choice2[0] == 1:
        openFilesFolder()
        return False

    clear()
    callibrateASCII(os.path.join(basepath,choice2[1]), os.path.join(basepath, choice[1]+'-res', 'func.cal'))
    return True

def calibrateData():
    basepath = 'files'
    files = os.listdir(basepath)

    files = [i for i in files if i not in [".DS_Store", 'config.json'] and '.' not in i and i[-4:] == '-res']
    files = [folder.replace('-res', '') for folder in files if 'func.cal' in os.listdir(os.path.join(basepath,folder))]
    choice = selectionWindow('Vælg kaliberingsfunktion',["<-- Gå tilbage", "[Klik her for at åbne mappe]"] + files)

    if choice[0] == 0: 
        return False
    
    if choice[0] == 1:
        openFilesFolder()
        return False
    
    return wrapper(callibrateSecondChoice, calibrateData, choice)



def excelCallibrateSecondChoice(choice):
    basepath = 'files'
    files = os.listdir(basepath)
    files = [i for i in files if i not in [".DS_Store", 'config.json'] and '.' not in i and i[-4:] == '-res']
    files = [folder.replace('-res', '') for folder in files if 'temperature' in os.listdir(os.path.join(basepath,folder))]
    choice2 = selectionWindow('Vælg datasæt',["<-- Gå tilbage", "[Klik her for at åbne mappe]"] + files)

    if choice2[0] == 0:
        return False
    
    if choice2[0] == 1:
        openFilesFolder()
        return False

    clear()
    callibrateExcelAndShow(os.path.join(basepath,choice2[1]+'-res'), os.path.join(basepath, choice[1]+'-res', 'func.cal'))
    return True


def excelCalibrateData():
    basepath = 'files'
    files = os.listdir(basepath)

    files = [i for i in files if i not in [".DS_Store", 'config.json'] and '.' not in i and i[-4:] == '-res']
    files = [folder.replace('-res', '') for folder in files if 'func.cal' in os.listdir(os.path.join(basepath,folder))]
    choice = selectionWindow('Vælg kaliberingsfunktion',["<-- Gå tilbage", "[Klik her for at åbne mappe]"] + files)

    if choice[0] == 0: 
        return False
    
    if choice[0] == 1:
        openFilesFolder()
        return False
    
    return wrapper(excelCallibrateSecondChoice, excelCalibrateData, choice)


def starLineExpress():
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
    showImage(os.path.join(basepath,choice[1]+'-res'))
    typereg = selectionWindow('Vælg type af regression',REGRESSIONSNAMES)
    resetColor()
    createRegression(os.path.join(basepath,choice[1]+'-res'), *REGRESSIONS[typereg[0]])
    return True


def regressionManual():
    basepath = 'files'
    files = os.listdir(basepath)

    files = [i.replace('-res', '') for i in files if i not in [".DS_Store", 'config.json'] and '.' not in i and i[-4:] == '-res']
    choice = selectionWindow('Vælg mappe',["<-- Gå tilbage", "[Klik her for at åbne mappe]"] + files)

    if choice[0] == 0: 
        return False
    
    if choice[0] == 1:
        openFilesFolder()
        return False
    
    clear()
    showImage(os.path.join(basepath,choice[1]+'-res'))
    typereg = selectionWindow('Vælg type af regression',REGRESSIONSNAMES)
    resetColor()
    createRegression(os.path.join(basepath,choice[1]+'-res'), *REGRESSIONS[typereg[0]])
    return True


def cameraConvertFolder():
    basepath = 'files'
    files = os.listdir(basepath)

    files = [i for i in files if i not in [".DS_Store", 'config.json'] and '.' not in i and i[-4:] != '-res']
    choice = selectionWindow('Vælg mappe',["<-- Gå tilbage", "[Klik her for at åbne mappe]"] + files)

    if choice[0] == 0: 
        return False
    
    if choice[0] == 1:
        openFilesFolder()
        return False
    
    clear()
    convertFolder(os.path.join(basepath,choice[1]))
    return True


def camera():
    
    # lav en "-res" til alle filer
    files = os.listdir('files')
    for i in files:
        if not(i not in [".DS_Store", 'config.json'] and '.' not in i and i[-4:] not in ['-res', '-cal']):continue
        createFolder(os.path.join('files',i+'-res'), remove=False)
    
    choice = selectionWindow('Termisk kamera',[
            "<-- Gå tilbage",
            "Dan kalliberingskurve",
            "Omdan til png",
            "Aflæs temperature",
            "Aflæs temperature [Manualt]",
            "Dan kallibreringskurve på data [Manuelt]",
            "Kallibrer datasæt [ASCII]",
            "Kallibrer allerede aflæst datasæt [excel]",
        ])

    if choice[0] == 0:
        return

    if choice[0] == 1:
        wrapper(starLineExpress, camera)

    if choice[0] == 2:
        wrapper(cameraConvertFolder, camera)

    if choice[0] == 3:
        wrapper(cameraGetTemperatures, camera)
    
    if choice[0] == 4:
        wrapper(cameraGetTemperatureManual, camera)

    if choice[0] == 5:
        wrapper(regressionManual, camera)

    if choice[0] == 6:
        wrapper(calibrateData, camera)

    if choice[0] == 7:
        wrapper(excelCalibrateData, camera)

def main():
    
    choice = selectionWindow('MP3 2023 Kalibrering af termisk måling',[
        "Termisk kamera",
        "Termokobler",
    ])

    if choice[0] == 0:
        wrapper(camera, main)

    if choice[0] == 1:
        wrapper(thermocouple, main)


def openFilesFolder():
    
    path = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'files')
    
    if platform.system() == 'Darwin':
        os.system('open {}'.format(path))
    elif platform.system() == 'Windows':
        os.system('start files')


if __name__ == '__main__':
    # init
    if len(sys.argv) >= 2 and sys.argv[1] == "init":
        setupAndInstall()
        sys.exit()

    if len(sys.argv) >= 2 and sys.argv[1] == "uninstall":
        uninstallPackages()
        sys.exit()

    # test
    if len(sys.argv) >= 2 and sys.argv[1] == "test":
        test()

    # normal
    else:
        main()
