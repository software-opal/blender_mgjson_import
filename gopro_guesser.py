from .mgjson import Outline
import itertools


def convert_lat_lon_alt(val):
    [lat, lon, alt] = val
    # lon is
    return (lon, lat, alt)


def gen_array_access(idx):
    return lambda val: val[idx]


def gen_axis_convert(axisOrder):
    if "x" not in axisOrder:
        yIdx = axisOrder.index("y")
        zIdx = axisOrder.index("z")
        return lambda val: (0, val[yIdx], val[zIdx])
    elif "y" not in axisOrder:
        xIdx = axisOrder.index("x")
        zIdx = axisOrder.index("z")
        return lambda val: (val[xIdx], 0, val[zIdx])
    elif "z" not in axisOrder:
        xIdx = axisOrder.index("x")
        yIdx = axisOrder.index("y")
        return lambda val: (val[xIdx], val[yIdx], 0)
    else:
        xIdx = axisOrder.index("x")
        yIdx = axisOrder.index("y")
        zIdx = axisOrder.index("z")
        return lambda val: (val[xIdx], val[yIdx], val[zIdx])


def guess_axis(outline: Outline):
    for perm in itertools.chain(
        itertools.permutations("xyz", 3), itertools.permutations("xyz", 2)
    ):
        if ",".join(perm) in outline.name:
            return gen_axis_convert(perm)
    return None
