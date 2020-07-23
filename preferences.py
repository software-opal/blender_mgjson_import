
# addon preferences in blender user preferences
# class AoMPreferences(AddonPreferences):
#     bl_idname = __name__

#     aom_path = StringProperty(
#             name="Path to Age of Mythology Installation",
#             subtype='FILE_PATH',
#             )
#     auto_import = BoolProperty(
#             name="Autmatically import images from AoM",
#             default=True,
#             )
#     comp_path = StringProperty(
#             name="Path to TextureExtractor.exe. (v2)",
#             subtype='FILE_PATH',
#             )
#     glob_tex = BoolProperty(
#             name="Default save converted textures globally. Default \"\\[AoM]\\Textures\\Converted\".",
#             default=True,
#             )
#     tex_path = StringProperty(
#             name="Path for global texture conversion storage.",
#             subtype='FILE_PATH',
#             )

#     def draw(self, context):
#         layout = self.layout
#         layout.label(text="Edit here your preferences to use the addon to it's fullest potential.")
#         layout.prop(self, "auto_import")
#         layout.prop(self, "aom_path")
#         layout.prop(self, "comp_path")
#         layout.prop(self, "glob_tex")
#         layout.prop(self, "tex_path")
