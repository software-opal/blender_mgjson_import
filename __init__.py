# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

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

def menu_func_import_single_mgjson(self, context):
    self.layout.operator(ImportSingleMgJson.bl_idname, text="Bake MGJSON to F-Curves")

def menu_func_import_single_mgjson(self, context):
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
