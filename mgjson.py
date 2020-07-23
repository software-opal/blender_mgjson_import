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
    if dataType["type"] == "numberString":
        return wrap_data_converter(Decimal, dataType=dataType)
    elif dataType["type"] in ["paddedString", "string", "number"]:
        return wrap_data_converter(lambda a: a, dataType=dataType)
    elif dataType["type"] == "numberStringArray":
        return wrap_data_converter(
            lambda arr: list(map(Decimal, arr)), dataType=dataType
        )
    else:
        raise ValueError(f"Unknown data type: {dataType!r}")


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
            sample.micros = int(
                (sample.time - startTime) / datetime.timedelta(microseconds=1)
            )

    return outline


ValueInnerType = typ.Union[int, float, Decimal, str]
ValueType = typ.Union[ValueInnerType, typ.List[ValueInnerType]]


@dataclass
class SamplePoint:

    time: datetime.datetime
    value: ValueType
    micros: typ.Optional[int] = None


def load_samples(
    sample_collection, parsed_outline
) -> typ.Tuple[datetime.datetime, typ.Dict[str, typ.List[SamplePoint]]]:
    startTime = None
    converted = {}
    for samples in sample_collection:
        key = samples["sampleSetID"]
        try:
            data_converter = get_data_converter(parsed_outline[key].dataType)
            convertedSamples = [
                SamplePoint(
                    time=parse_time(sample["time"]),
                    value=data_converter(sample["value"]),
                )
                for sample in samples["samples"]
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


@dataclass
class Outline:

    key: str
    type: str
    name: str
    interpolation: str
    dataType: typ.Dict
    value: typ.Union[None, ValueType, typ.List[SamplePoint]] = None

    def is_samples(self):
        if isinstance(self.value, list):
            return all(isinstance(v, SamplePoint) for v in self.value)
        else:
            return False

    def is_samples_numeric(self):
        return self.is_samples() and all(
            isinstance(v.value, (int, float, Decimal)) for v in self.value
        )

    def is_samples_list_of_numeric(self):
        return self.is_samples() and all(
            isinstance(v.value, list)
            and all(isinstance(i, (int, float, Decimal)) for i in v.value)
            for v in self.value
        )


def load_outline(outline):
    outline_items = {}
    for item in outline:
        key = item.get("sampleSetID") or item.get("matchName")
        data = Outline(
            key=key,
            type=item.get("objectType"),
            name=item.get("displayName") or key,
            interpolation=item.get("interpolation"),
            dataType=item.get("dataType"),
        )
        if data.type == "static":
            data.value = get_data_converter(data["dataType"])(item["value"])
        outline_items[key] = data
    return outline_items


# def merge_outlines(
#     outlines: typ.Dict[str, Outline], outlinesToConvert: typ.Dict[str, typ.List[str]]
# ):
#     outlines = dict(outlines)
#     for (outKey, inKeys) in outlinesToConvert.items():
#         assert outKey not in inKeys
#         inOutlines = [outlines[key] for key in inKeys]
#         inValuesToList = [
#             (lambda v: [v]) if outline.is_samples_numeric() else list
#             for outline in inOutlines
#         ]
#         inValuesIter = zip(outline.value for outline in inOutlines)
#         for values in inValuesIter:
#             mapped = itertools.chain.from_
