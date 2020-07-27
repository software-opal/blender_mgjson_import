from math import isclose, ceil
import pathlib
import datetime
import json

import bpy

# from bpy.props import *
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty

from .mgjson import load_file
from .gopro_guesser import (
    guess_axis,
    convert_lat_lon_alt,
    gen_array_access,
    gen_axis_convert,
)

# import function
class ImportMgJson(bpy.types.Operator, ImportHelper):
    """Import brg model files from Age of Mythology"""

    bl_idname = "import_scene.brg"
    bl_description = "Import MGJSON file animations to axises"
    bl_label = "Import MGJSON file"
    filename_ext = ".mgjson"
    filter_glob: StringProperty(default="*.mgjson", options={"HIDDEN"})

    filepath: StringProperty(
        name="File Path",
        description="Filepath used for importing the brg file",
        maxlen=1024,
        default="",
    )
    interpret_as_gopro: bpy.props.BoolProperty(
        name="Interpret file as Extracted GoPro Data", default=True
    )

    def execute(self, context):
        file = pathlib.Path(self.filepath)
        group_name = file.stem

        mgjson_group = context.scene.collection.children.get("MGJSON")
        if not mgjson_group:
            mgjson_group = bpy.data.collections.new("MGJSON")
            context.scene.collection.children.link(mgjson_group)

        target_group = mgjson_group.children.get(group_name)
        if not target_group:
            target_group = bpy.data.collections.new(group_name)
            mgjson_group.children.link(target_group)

        for obj in target_group.objects:
            target_group.objects.unlink(obj)
        target_group.hide_render = True

        raw_outlines = load_file(file)
        # Remove everything we can't render correctly.
        outlines = dict(
            filter(
                lambda kv: kv[1].is_samples_numeric_or_list_of_numeric(),
                raw_outlines.items(),
            )
        )
        self.report(
            {"DEBUG"},
            f"Found the following outlines: {', '.join(raw_outlines)}.\nAccepted: {', '.join(outlines)}",
        )
        if self.interpret_as_gopro:
            framerate = raw_outlines["framerate"].value
            start_frame = context.scene.frame_current
            scene_framerate = context.scene.render.fps / context.scene.render.fps_base
            if not isclose(framerate, scene_framerate):
                self.report(
                    {"INFO"},
                    f"FPS mismatch, Expecting a framerate of {framerate}, but got a framerate of {scene_framerate}",
                )

            # TODO: merge these two together to create a "Quarterion" orientation.
            # outlines = merge_outlines(outlines, {
            #     'stream1XCORIX': ['stream1XCORIX', 'stream1XCORIX2'],
            #     'stream1XIORIX': ['stream1XIORIX', 'stream1XIORIX2'],
            # })

            outlineKeys = [
                [
                    "stream1XACCLX",  # ACCL: Accelerometer (z,x,y) [m/s2]
                    "Accelerometer(m/s2)",
                    gen_axis_convert("zxy"),
                    render_xyz_coord,
                ],
                [
                    "stream1XGYROX",  # GYRO: Gyroscope (z,x,y) [rad/s]
                    "Gyroscope(rad/s)",
                    gen_axis_convert("zxy"),
                    render_xyz_coord,
                ],
                [
                    "stream1XGRAVX",  # GRAV: Gravity Vector
                    "Gravity Vector",
                    gen_axis_convert("zxy"),
                    render_xyz_coord,
                ],
                [
                    "stream1XGPS5X",  # GPS5: GPS (Lat.,Long.,Alt.) [deg,deg,m]
                    "GPS(lat,lon,alt)",
                    convert_lat_lon_alt,
                    render_xyz_coord,
                ],
                [
                    "stream1XGPS5X2",  # GPS5: GPS (2D speed,3D speed) [m/s,m/s]
                    "2D Speed(m/s)",
                    gen_array_access(0),
                    render_single_value_coord,
                ],
                [
                    "stream1XGPS5X2",  # GPS5: GPS (2D speed,3D speed) [m/s,m/s]
                    "3D Speed(m/s)",
                    gen_array_access(1),
                    render_single_value_coord,
                ],
            ]
            for [key, name, valueConv, valueRender] in outlineKeys:
                if key not in outlines:
                    continue
                outline = outlines[key]
                self.report(
                    {"INFO"},
                    f"Importing {name} from {key}. First point: {outline.value[0]}: {valueConv(outline.value[0].value)}",
                )
                with (file.with_suffix(f".{key}.json")).open("w") as f:
                    json.dump(
                        [(v.micros, valueConv(v.value)) for v in outline.value], f
                    )
                valueRender(
                    context,
                    target_group,
                    start_frame,
                    scene_framerate,
                    name,
                    outline.interpolation,
                    [(v.micros, valueConv(v.value)) for v in outline.value],
                )
        return {"FINISHED"}


MICROS_PER_SECOND = datetime.timedelta(seconds=1) / datetime.timedelta(microseconds=1)
INTERPOLATION_MAP = {"linear": "LINEAR", "hold": "CONSTANT"}


def convert_frame(start_frame, framerate, micros):
    return start_frame + (framerate * micros / MICROS_PER_SECOND)


def ensure_enough_frames(context, start_frame, framerate, timeCoords):
    max_frame = start_frame
    for (micro, coord) in timeCoords:
        max_frame = max(convert_frame(start_frame, framerate, micro), max_frame)
    context.scene.frame_end = max(context.scene.frame_end, max_frame)
    return max_frame


def render_xyz_coord(
    context, target_group, start_frame, framerate, name, interpolation, timeCoords
):
    max_frame = ensure_enough_frames(context, start_frame, framerate, timeCoords)
    axis = bpy.data.objects.new("empty", None)
    target_group.objects.link(axis)
    axis.name = name
    axis.empty_display_size = 2
    axis.empty_display_type = "ARROWS"
    axis.location.xyz = [0, 0, 0]
    axis.rotation_euler = [0, 0, 0]
    axis.keyframe_insert("location")
    fcurves = axis.animation_data.action.fcurves
    [xFcurve, yFcurve, zFcurve] = fcurves
    for (micro, coord) in timeCoords:
        frame = convert_frame(start_frame, framerate, micro)
        for value, fcurve in zip(coord, fcurves):
            kf = fcurve.keyframe_points.insert(frame, value, options={"FAST"})
            kf.interpolation = INTERPOLATION_MAP[interpolation]
    for fcurve in fcurves:
        fcurve.update()
        fcurve.convert_to_samples(start_frame, ceil(max_frame))


def render_single_value_coord(
    context, target_group, start_frame, framerate, name, interpolation, timeCoords
):
    max_frame = ensure_enough_frames(context, start_frame, framerate, timeCoords)
    axis = bpy.data.objects.new("empty", None)
    target_group.objects.link(axis)
    axis.name = name
    axis.empty_display_size = 2
    # Arrow points along +Z
    axis.empty_display_type = "SINGLE_ARROW"
    axis.location.xyz = [0, 0, 0]
    axis.rotation_euler = [0, 0, 0]
    # Only animate the z-axis.
    axis.keyframe_insert("location", 2)
    fcurve = axis.animation_data.action.fcurves[0]
    for (micro, value) in timeCoords:
        frame = convert_frame(start_frame, framerate, micro)
        kf = fcurve.keyframe_points.insert(frame, value, options={"FAST"})
        kf.interpolation = INTERPOLATION_MAP[interpolation]
    fcurve.update()
    fcurve.convert_to_samples(start_frame, ceil(max_frame))
