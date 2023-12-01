
from PIL import ImageDraw, Image
import numpy as np
import math

# def colorToValue(color):
#     return color[0] + color[1]*255 + color[2]*(255**2)


# def valueToColor(val):

#     v1 = val % 255
#     v2 = (val // 255) % 255
#     v3 = (val // (255**2))

#     return (v1, v2, v3)


def colorEqual(c1, c2):
    return all([c1[0]==c2[0], c1[1]==c2[1], c1[2]==c2[2]])


def drawCircle(mesh, center, radius, temp):

    
    for j, row in enumerate(mesh):

        for i, node in enumerate(row):
            
            d = math.sqrt((center[0]-i)**2+(center[1]-j)**2)

            if d < radius:
                mesh[j][i] = temp
    return mesh


def drawDonut(mesh, center, innerRadius, outerRadius, temp):

    
    for j, row in enumerate(mesh):

        for i, node in enumerate(row):
            
            d = math.sqrt((center[0]-i)**2+(center[1]-j)**2)

            if innerRadius < d < outerRadius:
                mesh[j][i] = temp
    return mesh


def drawRectangle(mesh, x, y, width, height, temp):

    color = (255,0,0)

    image = Image.new('RGB', (len(mesh[0]), len(mesh)))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0,0, image.width, image.height), fill=(0,0,0))

    draw.rectangle(
        [x,y,x+width,y+height],
        fill = color,
        outline = color
    )

    arr = np.array(image)
    for rowNum, row in enumerate(mesh):
        
        for colNum in range(len(row)):

            if colorEqual(arr[rowNum][colNum], color):
                mesh[rowNum][colNum] = temp

    return mesh
