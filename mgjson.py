import pathlib
import json

from decimal import Decimal
import functools
import datetime
import typing as typ

from dataclasses import dataclass



def wrap_data_converter(fn, *, dataType):
    @functools.wraps(fn)
    def wrapper(value):
        try:
            fn(value)
        except Exception:
            print(
                f"Exception raised whilst parsing.\n  value={value!r}\n  dataType={dataType!r}"
            )
            raise

    return wrapper


def default_data_converter(value):
    raise ValueError(f"Not implemented")


def get_data_converter(dataType):
    converter = default_data_converter
    if dataType["type"] == "numberString":
        converter = Decimal
    elif dataType["type"] in ["paddedString", "string", "number"]:
        converter = lambda a: a
    elif dataType["type"] == "numberStringArray":
        converter = lambda arr: list(map(Decimal, arr))
    else:
        raise ValueError(f"Unknown data type: {dataType!r}")
    return wrap_data_converter(converter, dataType=dataType)


def parse_time(time):
    if len(time) == 24 and time[23] == "Z":
        return datetime.datetime.fromisoformat(time[:23]).replace(
            tzinfo=datetime.timezone.utc
        )
    else:
        return datetime.datetime.fromisoformat(time)




def load_file(path):
    with pathlib.Path(path).open("r") as f:
        mgjson = json.load(f)
    outline = load_outline(mgjson["dataOutline"])

    (startTime, sample_collection) = load_samples(mgjson["dataDynamicSamples"], outline)

    for key, samples in sample_collection.items():
        outline[key].value = samples
        for sample in samples:
            sample.micros = int( (sample.time - startTime) / datetime.timedelta(microseconds=1))

    return outline

ValueInnerType = typ.Union[int, float, Decimal, str]
ValueType = typ.Union[ValueInnerType, typ.List[ValueInnerType]]

@dataclass
class Outline:

    key: str
    type: str
    name: str
    interpolation: str
    dataType: typ.Dict
    value: typ.Optional[ValueType] = None


def load_outline(outline):
    outline_items = {}
    for item in outline:
        key = item.get("sampleSetID") or item.get("matchName")
        data = Outline(
            key= key,
            type= item.get("objectType"),
            name= item.get("displayName") or key,
            interpolation= item.get("interpolation"),
            dataType= item.get("dataType"),
        )
        if data.type == "static":
            data.value = get_data_converter(data["dataType"])(item["value"])
        outline_items[key] = data
    return outline_items


@dataclass
class SamplePoint:

    time: datetime.datetime
    value: ValueType
    micros: typ.Optional[int] = None


def load_samples(sample_collection, parsed_outline) -> typ.Tuple[datetime.datetime, typ.Dict[str, typ.List[SamplePoint]]]:
    startTime = None
    converted = {}
    for samples in sample_collection:
        key = samples["sampleSetID"]
        try:
            dataConverter = get_data_converter(parsed_outline[key].dataType)
            convertedSamples = [
                SamplePoint(
                    time= parse_time(sample["time"]),
                    value= dataConverter(sample["value"]),)
                for sample in samples['samples']
            ]
            converted[key] = convertedSamples
            if convertedSamples:
                if startTime is None:
                    startTime = convertedSamples[0].time
                else:
                    startTime = min([startTime, convertedSamples[0].time])
        except Exception:
            print(f"Unable to parse samples for {key!r}")
            raise

    return (startTime, converted)
