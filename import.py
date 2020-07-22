
import bpy
import os
import pathlib
from bpy.props import *
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty

#import function
class ImportMgJson(bpy.types.Operator, ImportHelper):
    '''Import brg model files from Age of Mythology'''
    bl_idname = "import_scene.brg"
    bl_description = "Import MGJSON file animations to axises"
    bl_label = "Import MGJSON file"
    filename_ext = ".mgjson"
    filter_glob = StringProperty(default="*.mgjson", options={'HIDDEN'})

    filepath = StringProperty(name="File Path",
        description="Filepath used for importing the brg file",
        maxlen=1024, default="")

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
