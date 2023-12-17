
import os
import subprocess
import sys

packages = {
    "psutil",
    "logging",
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
    if input('Fortsæt [y/n] ').lower() != 'y':
        return

    for package in packages:
        install(package)

def uninstallPackages():
    for package in packages:
        uninstall(package)