# ##### BEGIN GPL LICENSE BLOCK #####
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####
bl_info = {
    "name": "Unitypackage Importer",
    "description": "Import models (meshes + textures) from scenes in .unitypackage files.",
    "author": "JackTheFoxOtter",
    "version": (1, 0),
    "blender": (3, 1, 2),
    "location": "File > Import > Import from Unitypackage",
    "warning": "",
    "wiki_url": "https://github.com/JackTheFoxOtter/blender-unitypackage-importer",
    "tracker_url": "https://github.com/JackTheFoxOtter/blender-unitypackage-importer/issues",
    "support": "COMMUNITY",
    "category": "Import",
}

"""
Import models (meshes + textures) from scenes in .unitypackage files.

"""
import bpy
from bpy.props import CollectionProperty
from .operators import *


classes = (
    UNITYPACKAGE_IMPORTER_PG_import_list_item,
    UNITYPACKAGE_IMPORTER_PG_import_display_list_item,
    UNITYPACKAGE_IMPORTER_UL_import_list,
    UNITYPACKAGE_IMPORTER_OT_select_all,
    UNITYPACKAGE_IMPORTER_OT_deselect_all,
    UNITYPACKAGE_IMPORTER_OT_import_unitypackage,
    UNITYPACKAGE_IMPORTER_OT_import_unitypackage_modal,
)


def import_unitypackage_menu_draw(self, context):
    # Draw function for operator in import menu
    self.layout.operator(UNITYPACKAGE_IMPORTER_OT_import_unitypackage.bl_idname, text="Import from Unitypackage")


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.WindowManager.unitypackage_importer_import_list = CollectionProperty(type=UNITYPACKAGE_IMPORTER_PG_import_list_item)
    bpy.types.WindowManager.unitypackage_importer_import_display_list = CollectionProperty(type=UNITYPACKAGE_IMPORTER_PG_import_display_list_item)
    bpy.types.WindowManager.unitypackage_importer_import_display_list_index = IntProperty(default = 0)

    bpy.types.TOPBAR_MT_file_import.append(import_unitypackage_menu_draw)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(import_unitypackage_menu_draw)
    
    del bpy.types.WindowManager.unitypackage_importer_import_list
    del bpy.types.WindowManager.unitypackage_importer_import_display_list
    del bpy.types.WindowManager.unitypackage_importer_import_display_list_index

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

