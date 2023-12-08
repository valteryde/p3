
import ast
import operator as op
from .loader import loadASCIIFile, saveASCIIFile, createFolder
import glob
import os 
import tqdm
import kaxe
import openpyxl as pxl

#https://stackoverflow.com/questions/2371436/evaluating-a-mathematical-expression-in-a-string
# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}

def eval_expr(expr):
    """
    >>> eval_expr('2^6')
    4
    >>> eval_expr('2**6')
    64
    >>> eval_expr('1 + 2*3**(4^5) / (6 + -7)')
    -5.0
    """
    return eval_(ast.parse(expr, mode='eval').body)


def eval_(node):
    if isinstance(node, ast.Num): # <number>
        return node.n
    elif isinstance(node, ast.BinOp): # <left> <operator> <right>
        return operators[type(node.op)](eval_(node.left), eval_(node.right))
    elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
        return operators[type(node.op)](eval_(node.operand))
    else:
        raise TypeError(node)

notcal, cal = 0, 0
def loadCalFunction(calfile:str):
    file = open(calfile, 'r')
    funcs = file.read().split('\n')

    for i, line in enumerate(funcs):

        interval, func = line.split(':')
        interval = interval.split(',')
        funcs[i] = ((float(interval[0]), float(interval[1])), func)

    def func(T):
        global notcal, cal

        for interval, f in funcs:

            if interval[0] <= T < interval[1]:
                cal += 1
                return eval_expr(f.replace('x', str(T)))

        notcal += 1
        return T

    file.close()
    return func

def createCalFunction(fname,func):
    
    file = open(fname, 'w')
    file.write('\n'.join(['{},{}:{}'.format(i[0][0],i[0][1],i[1]) for i in func]))
    file.close()


def callibrateASCII(asciifolder, calfile):
    global notcal, cal
    notcal, cal = 0, 0
    
    calfunc = loadCalFunction(calfile)

    outputfolder = asciifolder+'-cal'
    createFolder(outputfolder)
    files = glob.glob(os.path.join(asciifolder, '*.asc'))

    pbar = tqdm.tqdm(total=len(files))
    freq = 100
    for i, file in enumerate(files):
        if i % freq != 0: continue

        data, _, _, raw = loadASCIIFile(file, getRaw=True)

        for rowNum,row in enumerate(data):
            
            for colNum, temp in enumerate(row):
                data[rowNum][colNum] = str(calfunc(temp))

        saveASCIIFile(os.path.join(outputfolder,os.path.split(file)[-1]), data, raw)
        pbar.update(freq)

    pbar.close()
    print('Callibrated {} temperatures, ignored {} temperatures'.format(cal, notcal))
    print('Output:',outputfolder)


def callibrateExcel(folder, calfile):
    global notcal, cal
    notcal, cal = 0, 0
    
    calfunc = loadCalFunction(calfile)

    xlsxfolderpath = os.path.join(folder,'temperature')
    outputfolder = os.path.join(folder, 'calibrated')
    createFolder(outputfolder)
    files = glob.glob(os.path.join(xlsxfolderpath, '*.xlsx'))

    for file in files:
        workbook = pxl.Workbook()
        sheet = workbook.active
        data = kaxe.data.loadExcel(file, 'Sheet', (1,1), (4,-1))
        pbar = tqdm.tqdm(total=len(data))

        for t1, t2, t3, t4 in data:
            sheet.append((calfunc(t1), calfunc(t2), calfunc(t3), calfunc(t4)))
            pbar.update()
        pbar.close()
        workbook.save(os.path.join(outputfolder,os.path.split(file)[-1]))
        workbook.close()

    print('Callibrated {} temperatures, ignored {} temperatures'.format(cal, notcal))
    print('Output:',outputfolder)
