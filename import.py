from math import isclose
import pathlib
import datetime

import bpy
# from bpy.props import *
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty

from .mgjson import load_file
from .gopro_guesser import guess_axis, convert_lat_lon_alt, gen_array_access, gen_axis_convert

# import function
class ImportMgJson(bpy.types.Operator, ImportHelper):
    """Import brg model files from Age of Mythology"""

    bl_idname = "import_scene.brg"
    bl_description = "Import MGJSON file animations to axises"
    bl_label = "Import MGJSON file"
    filename_ext = ".mgjson"
    filter_glob = StringProperty(default="*.mgjson", options={"HIDDEN"})

    filepath: StringProperty(
        name="File Path",
        description="Filepath used for importing the brg file",
        maxlen=1024,
        default="",
    )
    interpret_as_gopro: bpy.props.BoolProperty(
        name="Interpret file as Extracted GoPro Data"
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

        outlines = load_file(file)
        # Remove everything we can't render correctly.
        outlines = dict(
            filter(
                lambda kv: kv[1].is_value_numeric() or kv[1].is_value_list_of_numeric(),
                outlines.items(),
            )
        )
        if self.interpret_as_gopro:
            framerate = outlines["framerate"].value
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
                valueRender(
                    target_group,
                    start_frame,
                    scene_framerate,
                    name,
                    outline.interpolation,
                    [(v.millis, valueConv(v.value)) for v in outline.value],
                )


MICROS_PER_SECOND = datetime.timedelta(seconds=1) / datetime.timedelta(microseconds=1)
INTERPOLATION_MAP = {"linear": "LINEAR", "hold": "CONSTANT"}


def render_xyz_coord(
    target_group, start_frame, framerate, name, interpolation, timeCoords
):
    axis = bpy.data.objects.new("empty", None)
    target_group.objects.link(axis)
    axis.name = name
    axis.empty_display_size = 2
    axis.empty_display_type = "ARROWS"
    axis.location.xyz = [0, 0, 0]
    axis.rotation_euler = [0, 0, 0]
    fcurves = axis.driver_add("location")
    [xFcurve, yFcurve, zFcurve] = fcurves
    for (micros, coord) in timeCoords:
        frame = micros / framerate / MICROS_PER_SECOND
        for value, fcurve in zip(coord, fcurves):
            kf = fcurve.keyframe_points.insert(frame, value, options={"FAST"})
            kf.interpolation = INTERPOLATION_MAP[interpolation]
    for fcurve in fcurves:
        fcurve.update()
        fcurve.convert_to_samples()


def render_single_value_coord(
    target_group, start_frame, framerate, name, interpolation, timeCoords
):
    axis = bpy.data.objects.new("empty", None)
    target_group.objects.link(axis)
    axis.name = name
    axis.empty_display_size = 2
    # Arrow points along +Z
    axis.empty_display_type = "SINGLE_ARROW"
    axis.location.xyz = [0, 0, 0]
    axis.rotation_euler = [0, 0, 0]
    # Only animate the z-axis.
    fcurve = axis.driver_add("location", 2)
    for (micros, value) in timeCoords:
        frame = micros / framerate / MICROS_PER_SECOND
        kf = fcurve.keyframe_points.insert(frame, value, options={"FAST"})
        kf.interpolation = INTERPOLATION_MAP[interpolation]
    fcurve.update()
    fcurve.convert_to_samples()
