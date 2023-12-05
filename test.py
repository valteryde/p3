
from camera import createRegression, showImage
from kaxe import resetColor

# def main():
#     # convertFolder('files/data-2')
#     # analyze("/Users/valterdaugberg/skole/p3/ship/master/files/data-1/irdata_0010_0010.asc")
    
#     # analyze("/Users/valterdaugberg/skole/p3/ship/master/files/data-1/irdata_0016_0016.asc")
#     # createMaskFromFrame("/Users/valterdaugberg/skole/p3/ship/master/files/data-2/irdata_0011_0100.asc")
#     res = analyzeFromFolder('files/data-2', 'test.xlsx', 10)

def main():
    
    class bcolors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKCYAN = '\033[96m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
    
    showImage('files/Forsøg 13-res')
    resetColor()
    createRegression('files/Forsøg 13-res')