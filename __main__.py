
from interface import selectionWindow, displayData
from interface import selectWrapper as wrapper
from thermocouple import GLOBALVARS, serial_ports, handleCommunication, getNow
from camera import analyzeFromFolder, convertFolder
from _thread import start_new_thread
import datetime
import os
import logging
import platform
import sys

if len(sys.argv) >= 2 and sys.argv[2] == "init":
    os.mkdir('files')
    file = open(os.path.join('files', 'config.json'), 'w')
    file.close()
    os.mkdir('debug')

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
        ("Tidspunkt", getNow),
        ("Sidst gemt", lambda: GLOBALVARS["last_save"]),
        ("Output", lambda: GLOBALVARS["output_filename"])
    ])


def cameraGetTemperatures():
    basepath = 'files'
    files = os.listdir(basepath)

    files = [i for i in files if i not in [".DS_Store", 'config.json'] and '.' not in i]

    choice = selectionWindow('Vælg mappe',["<-- Gå tilbage", "[Klik her for at åbne mappe]"] + files)

    if choice[0] == 0: 
        return False
    
    if choice[0] == 1:
        openFilesFolder()
        return False
    
    if '.asc' in choice[1]: #file
        pass
    
    else: #folder
        os.system('clear')
        analyzeFromFolder(os.path.join(basepath,choice[1]))
        return True


def cameraConvertFolder():
    basepath = 'files'
    files = os.listdir(basepath)

    files = [i for i in files if i not in [".DS_Store", 'config.json'] and '.' not in i]

    choice = selectionWindow('Vælg mappe',["<-- Gå tilbage", "[Klik her for at åbne mappe]"] + files)

    if choice[0] == 0: 
        return False
    
    if choice[0] == 1:
        openFilesFolder()
        return False
    
    os.system('clear')
    convertFolder(os.path.join(basepath,choice[1]))
    return True


def camera():
    
    choice = selectionWindow('Termisk kamera',[
            "<-- Gå tilbage",
            "Omdan til png",
            "Aflæs temperature [ASCII]",
        ])

    if choice[0] == 0:
        return

    if choice[0] == 1:
        wrapper(cameraConvertFolder, camera)

    if choice[0] == 2:
        wrapper(cameraGetTemperatures, camera)


def main():
    
    choice = selectionWindow('MP3 2023 Kalibrering af termisk måling',[
        "Termokobler",
        "Termisk kamera",
        # "Simulation",
    ])

    if choice[0] == 0:
        wrapper(thermocouple, main)

    if choice[0] == 1:
        wrapper(camera, main)


def openFilesFolder():
    
    path = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'files')
    
    if platform.system() == 'Darwin':
        os.system('open {}'.format(path))
    elif platform.system() == 'Windows':
        os.system('start files')


if __name__ == '__main__':
    main()