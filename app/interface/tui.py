from curses import wrapper
from curses.textpad import Textbox, rectangle
import curses
import logging
import os
import time

logging.basicConfig(filename=os.path.join('debug','log.log'),
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)


def __selectionWindow(stdscr, title:str, selections:list):

    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE) #blue on red
    COLORS = curses.color_pair(1)
    
    stdscr.clear()
    stdscr.refresh()

    stdscr.addstr(0,0,title)
    maxWidth = max([len(i) for i in selections])
    stdscr.addstr(1,0,'-'*maxWidth)
    selwindow = curses.newwin(len(selections), maxWidth, 2, 0)
    stdscr.addstr(len(selections)+2,0,'-'*maxWidth)

    try:
        selwindow.addstr(0, 0, selections[0], COLORS)
    except curses.error:
        pass
    
    for i, item in enumerate(selections[1:]):
        try:
            selwindow.addstr(i+1, 0, item)
        except curses.error:
            pass

    selwindow.refresh()
    
    cursor = 0
    lastPos = 0
    while True:
        key = stdscr.getkey()

        # move
        if key == "KEY_LEFT":
            cursor -= 1
        
        elif key == "KEY_RIGHT":
            cursor += 1

        elif key == "KEY_UP":
            cursor -= 1

        elif key == "KEY_DOWN":
            cursor += 1
        
        elif key == "KEY_ENTER" or key == "\n":
            break
        
        if cursor < 0:
            cursor = len(selections) - 1
        
        if cursor + 1 > len(selections):
            cursor = 0

        try:
            selwindow.addstr(cursor, 0 ,selections[cursor], COLORS)
        except curses.error:
            pass
        
        if lastPos != cursor:
            try:
                selwindow.addstr(lastPos, 0 ,selections[lastPos])
            except curses.error:
                pass

        selwindow.refresh()
        lastPos = cursor

    return (cursor, selections[cursor])

def selectionWindow(title:str, selections:list):
    return wrapper(__selectionWindow, title, selections)


def __displayData(stdscr, data:list):    
    stdscr.clear()
    stdscr.refresh()
    curses.curs_set(0)

    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(6, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    COLORS = {
        "RED": 2,
        "BLUE": 3,
        "GREEN": 4,
        "WHITE":5,
        "YELLOW": 6,
    }



    while True:
        stdscr.clear()

        for i, d in enumerate(data):
            title, func = d

            funcres = func()
            if type(funcres) in [tuple, list]:
                color = curses.color_pair(COLORS[funcres[1]])
                stdscr.addstr(i, 0, title+':')
                stdscr.addstr(i, len(title)+1, str(funcres[0]), color)
            else:
                stdscr.addstr(i, 0, '{}:{}'.format(title, str(funcres)))

        stdscr.addstr(i+2, 0 ,'Press [CTRL-C] to exit')
        stdscr.refresh()
        time.sleep(0.05)


def displayData(data):
    return wrapper(__displayData, data)
