
bl_info = {
    "name": "mgjson-import",
    "author": "Opal Symes",
    "description": "",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Generic",
}

import bpy

# def menu_func_import_single_mgjson(self, context):
#     self.layout.operator(ImportSingleMgJson.bl_idname, text="Bake MGJSON to F-Curves")

def menu_func_import_mgjson(self, context):
    self.layout.operator(ImportMgJson.bl_idname, text="MGJSON (.mgjson)")


def register():
    bpy.utils.register_module(__name__)
    reload_scripts()
    # bpy.types.GRAPH_MT_key.append(menu_func_import_single_mgjson)
    bpy.types.INFO_MT_file_import.append(menu_func_import_mgjson)


def unregister():
    bpy.utils.unregister_module(__name__)
    # bpy.types.GRAPH_MT_key.remove(menu_func_import_single_mgjson)
    bpy.types.INFO_MT_file_import.append(menu_func_import_mgjson)


def reload_scripts():  # reload all subscripts when reloading main script
    ...
    # reload(brg_util)
    # reload(brg_import)
    # reload(brg_export)
