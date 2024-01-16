
from .loader import loadASCIIFile

def __getTempFromFrameWithMaskSingle(fpath, mask, maskpos):
    data, _, _ = loadASCIIFile(fpath)

    return {
        1:data[200][200],
        2:data[200][200],
        3:data[200][200],
        4:data[200][200]
    }

