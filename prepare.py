
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
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def uninstall(package):
    subprocess.check_call([sys.executable, "-m", "pip", "uninstall", package])

def setupAndInstall():
    if not os.path.exists('files'): os.mkdir('files')
    if not os.path.exists('debug'): os.mkdir('debug')

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
