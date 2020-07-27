
bl_info = {
    "name": "mgjson-import",
    "author": "Opal Symes",
    "description": "MGJSON Import",
    "blender": (2, 83, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Import-Export",
}

import bpy
from .mgimport import ImportMgJson

classes = (
    ImportMgJson,
)

# def menu_func_import_single_mgjson(self, context):
#     self.layout.operator(ImportSingleMgJson.bl_idname, text="Bake MGJSON to F-Curves")

def menu_func_import_mgjson(self, context):
    self.layout.operator(ImportMgJson.bl_idname, text="MGJSON (.mgjson)")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_mgjson)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_mgjson)
