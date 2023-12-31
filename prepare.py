
import os
import subprocess
import sys
import platform

packages = {
    "psutil",
    "logging",
    "openpyxl",
    "pyserial",
    "tqdm",
    "numpy",
    "Pillow",
    "pyglet",
    "scipy",
    "sympy"
}

# macpackages = {}

windowpackages = {
    "windows-curses",
}

def install(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except Exception as e:
        print('[ERROR]',e)

def uninstall(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", package])
    except Exception as e:
        print('[ERROR]',e)

def createFolders():
    if not os.path.exists('files'): os.mkdir('files')
    if not os.path.exists('debug'): os.mkdir('debug')

def setupAndInstall():
    createFolders() #for sikkerheds skyld

    print('Der installers nu nogle pakker som programmet bruger')
    print('Disse kan altid afinstalleres med ')
    print('\033[93m>>python3 app uninstall\033[0m')
    if input('Fortsæt? [y/n] ').lower() != 'y':
        return

    for package in packages:
        install(package)

    if platform.system().lower() == 'windows':
        for package in windowpackages:
            install(package)

    # if platform.system().lower() == 'darwin':
    #     for package in macpackages:
    #         install(package)


def uninstallPackages():
    for package in packages:
        uninstall(package)
    
    # jeg kan ikke få lov til at slette windows-curses
    # tja
