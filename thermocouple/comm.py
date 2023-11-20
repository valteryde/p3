
#firmdata has to be installed on arduiono

#communication.py
import logging
from .globs import GLOBALVARS
import time
import openpyxl as pxl
import datetime
import os
import serial

# mokeypatch (https://github.com/pyinvoke/invoke/issues/833)
import inspect

if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec


def getNow():
    now = datetime.datetime.now()
    
    hour = now.hour
    minute = now.minute
    second = now.second

    if hour < 10:
        hour = '0' + str(hour)

    if minute < 10:
        minute = '0' + str(minute)
    
    if second < 10:
        second = '0' + str(second)

    return '{}-{}-{}'.format(str(hour), str(minute), str(second))

def getNowDate():
    now = datetime.datetime.now()
    
    year = now.year
    month = now.month
    date = now.day

    if month < 10:
        month = '0' + str(month)
    
    if date < 10:
        date = '0' + str(date)

    return '{}-{}-{}'.format(str(year), str(month), str(date))


def openNewSheet():
    relFilePath = os.path.join('files','tc-{}-{}.xlsx'.format(getNowDate(),getNow()))
    GLOBALVARS['output_filename'] = relFilePath
    workbook = pxl.Workbook()
    sheet = workbook.active
    sheet.append(['Epoch [s]', 'H:M:S', 'Tid siden start [s]', 'Temperatur [C]'])
    return workbook, sheet, relFilePath


def handleCommunication(port): #over firmdata, much safer
    workbook, sheet, filepath = openNewSheet()
    
    saveFreq = 100
    restartFreq = 5000

    try:
        GLOBALVARS["state"] = "Starting"
        try:
            ser = serial.Serial(port, 38400)
        except Exception:
            GLOBALVARS["state"] = "Failed to open"
            return

        UPDATETIME = 0.25

        c = 0
        startTime = time.time()
        while True:
            now = time.time()
            temp = str(ser.readline().decode()) #UTF-8
            temp = temp.replace('\n', '')
            GLOBALVARS["state"] = "Online"

            GLOBALVARS["temp"] = temp
            sheet.append([now, getNow(), now - startTime, float(temp)])
            if c % saveFreq == 0: 
                workbook.save(filepath)
                GLOBALVARS["last_save"] = getNow()
            c += 1
            GLOBALVARS['data_points_count'] = c

            if c % restartFreq == 0:
                workbook.save(filepath)
                workbook.close()
                workbook, sheet, filepath = openNewSheet()

            time.sleep(0.05)

    except Exception as e:
        logging.debug(e)
        GLOBALVARS["state"] = "Offline"
    
    workbook.save(filepath)
    workbook.close()

if __name__ == '__main__':
    handleCommunication('/dev/cu.usbmodem114401')

