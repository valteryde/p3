
from interface import selectionWindow, displayData
from interface import selectWrapper as wrapper
from thermocouple import GLOBALVARS, serial_ports, handleCommunication, getNow
from camera import analyzeFromFolder, createRegression, showImage
from camera import convertFolder, analyzeFromFolderManual
from camera import callibrateASCII
from camera import createFolder
from test import main as test
from _thread import start_new_thread
import datetime
import os
import logging
import platform
import sys
import math
import psutil
from kaxe import resetColor
# from .install import 

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



def starLineExpress():
    basepath = 'files'
    files = os.listdir(basepath)

    files = [i for i in files if i not in [".DS_Store", 'config.json'] and '.' not in i and i[-4:] != '-res']
    choice = selectionWindow('Vælg mappe',["<-- Gå tilbage", "[Klik her for at åbne mappe]"] + files)

    if choice[0] == 0: 
        return False
    
    if choice[0] == 1:
        openFilesFolder()
        return False
    
    analyzeFromFolder(os.path.join(basepath,choice[1]), 'files')
    print('\033[96m'+'Når denne process er færdig, vil dataen blive vist på en graf. Læg her mærke til hop i HDR. Disse værdier skal bruges efterfølgende'+'\033[0m')
    showImage(os.path.join(basepath,choice[1])+'-res')
    resetColor()
    clear()
    createRegression(os.path.join(basepath,choice[1])+'-res')
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
    createRegression(os.path.join(basepath,choice[1]+'-res'))
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
            "Kallibrer datasæt",
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
        os.mkdir('files')
        os.mkdir('debug')

    # test
    if len(sys.argv) >= 2 and sys.argv[1] == "test":
        test()

    # normal
    else:
        main()
