"""
==========
Histograms
==========

How to plot histograms with Matplotlib.
"""

from kaxe import *
import numpy as np
import os

def cum(data):
    
    sm = 0
    res = []
    for i in data:
        sm += i
        res.append(sm)
    return res


def makeHist(data, fname):
    
    bins = np.arange(max(*data[0], *data[1]))
    a1, b1 = np.histogram(data[0], bins, density=True)
    a2, b2 = np.histogram(data[1], bins, density=True)
    
    plt = Plot([None, None, 0, None])
    plt.title(first='Temperatur', second='Frekvens')

    p1 = objects.Points(b1, a1, connect=True).legend('Før')
    p2 = objects.Points(b2, a2, connect=True).legend('Efter')
    
    plt.add(p1)
    plt.add(p2)

    plt.save(os.path.join('debug','hist.png'))
    
    # cum
    plt = Plot([None, None, 0, 1])
    plt.title(first='Temperatur', second='Kumuleret frekvens')

    p1 = objects.Points(b1, cum(a1), connect=True).legend('Før')
    p2 = objects.Points(b2, cum(a2), connect=True).legend('Efter')
    
    plt.add(p1)
    plt.add(p2)

    plt.save(os.path.join('debug','cum-hist.png')) 