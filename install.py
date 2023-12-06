
import subprocess
import sys

#https://stackoverflow.com/questions/12332975/how-can-i-install-a-python-module-within-code
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])