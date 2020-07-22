from .mgjson import Outline
import itertools

def genAxisConvert(axisOrder):
    xIdx = axisOrder.index('x')
    yIdx = axisOrder.index('y')
    zIdx = axisOrder.index('z')

    return lambda val: (val[xIdx], val[yIdx], val[zIdx])


def guessAxis(outline: Outline):
    for perm in itertools.permutations('xyz', 3):
        if ','.join(perm) in outline.name:
            return genAxisConvert(perm)
