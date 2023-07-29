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
import bpy
import logging
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper
from bpy.props import BoolProperty, IntProperty, StringProperty, EnumProperty
from .config import log_level
from .modules.unitypackage_parser import UnitypackageParser
from .importing import prepare_direct_import, do_direct_import, prepare_resolved_import, do_resolved_import


logger = logging.getLogger("Import Unitypackage")
logger.setLevel(log_level)


def update_import_list(self, context):
    """
    Updates visibility and enabled states for all items.
    Also creates display items for all visible items.
    
    """
    # Get global lists
    import_list = context.window_manager.unitypackage_importer_import_list
    import_display_list = context.window_manager.unitypackage_importer_import_display_list

    # Clear display list
    import_display_list.clear()

    # Reference loading indicator
    # wm = context.window_manager
    # wm.progress_begin(0, len(files))
    # wm.progress_update(i)
    # wm.progress_end()
    
    # Iterate over items and update visibility
    hierachy_stack = []
    prev_item = None
    for index, item in enumerate(import_list):
        if prev_item:
            if item.indentation > prev_item.indentation:
                # Entered hierachy level
                hierachy_stack.append(prev_item)
            elif item.indentation < prev_item.indentation:
                # Left hierachy level(s)
                hierachy_stack = hierachy_stack[:(item.indentation - prev_item.indentation)]
        
        # Determine hierachy parent item if there is one    
        parent_item = hierachy_stack[-1] if hierachy_stack else None
        
        # Determine own enabled state
        item.is_enabled = not parent_item or parent_item.is_enabled and parent_item.is_selected
        
        # Determine own visibility
        item.is_visible = not parent_item or parent_item.is_visible and parent_item.is_expanded
        if item.is_visible:
            # Item is visible, create display item
            display_item = import_display_list.add()
            display_item.referenced_item_index = index
        
        # Set prev_item for next iteration
        prev_item = item


class UNITYPACKAGE_IMPORTER_PG_import_list_item(bpy.types.PropertyGroup):
    """
    Represents an importable asset from a .unitypackage file.
    Can be selected or unselected for the final import.
    
    """
    bl_idname = 'UNITYPACKAGE_IMPORTER_PG_import_list_item'

    name : StringProperty(name="Name")
    guid : StringProperty(name="GUID")
    icon : StringProperty(name="Icon", default='NONE')
    indentation : IntProperty(name="Indentation", default=0)
    is_selected : BoolProperty(name="Selected", default=False, update=update_import_list)
    is_expanded : BoolProperty(name="Expanded", default=False, update=update_import_list)
    is_enabled : BoolProperty(name="Enabled", default=True)
    is_visible : BoolProperty(name="Visible", default=False)


class UNITYPACKAGE_IMPORTER_PG_import_display_list_item(bpy.types.PropertyGroup):
    """
    Item used for displaying list entries. References a UnityImportListItem.
    This is necessary because we can't skip rendering items in the UI list,
    so we need a second, "display list" which is updated based on item visibility.
    
    """
    bl_idname = 'UNITYPACKAGE_IMPORTER_PG_import_display_list_item'

    referenced_item_index : IntProperty(name="Reference Item Index")


class UNITYPACKAGE_IMPORTER_UL_import_list(bpy.types.UIList):
    """
    UI List for import items.
    
    """
    bl_idname = 'UNITYPACKAGE_IMPORTER_UL_import_list'
    layout_type = 'GRID'
    
    def draw_item(self, context, layout, data, display_item, icon, active_data, active_propname, index):
        # Determine referenced and next item for this display item
        import_list = context.window_manager.unitypackage_importer_import_list
        item_index = display_item.referenced_item_index
        item = import_list[item_index]
        next_item = import_list[item_index + 1] if item_index < len(import_list) - 1 else None
        
        row = layout.row(align=True)
        
        # Indentation
        for i in range(item.indentation):
            row.separator(factor=3)
        
        # Draw expand arrow or empty space
        if next_item and next_item.indentation > item.indentation:
            expanded_icon = 'TRIA_DOWN' if item.is_expanded else 'TRIA_RIGHT'
            row.prop(item, "is_expanded", text="", icon=expanded_icon, emboss=False)
        else:
            row.separator(factor=3)
        
        # Label & Checkbox
        row.label(text=item.name, icon=item.icon)
        row.prop(item, "is_selected", text="")
        
        # Enabled state
        row.enabled=item.is_enabled

    def draw_filter(self, context, layout):
        """UI code for the filtering/sorting/search area."""

        layout.separator()
        col = layout.column(align=True)

        row = col.row(align=True)
        row.prop(self, 'filter_name', text='', icon='VIEWZOOM')
        row.prop(self, 'use_filter_invert', text='', icon='ARROW_LEFTRIGHT')


class UNITYPACKAGE_IMPORTER_OT_select_all(bpy.types.Operator):
    """
    Operator to select all import items.
    
    """
    bl_idname = "unitypackage_importer.select_all"
    bl_label = "Select All"
    
    def execute(self, context):
        import_list = context.window_manager.unitypackage_importer_import_list
        for item in import_list:
            item.is_selected = True
        return { 'FINISHED' }


class UNITYPACKAGE_IMPORTER_OT_deselect_all(bpy.types.Operator):
    """
    Operator to deselect all import items.
    
    """
    bl_idname = "unitypackage_importer.deselect_all"
    bl_label = "Deselect All"
    
    def execute(self, context):
        import_list = context.window_manager.unitypackage_importer_import_list
        for item in import_list:
            item.is_selected = False
        return { 'FINISHED' }


class UNITYPACKAGE_IMPORTER_OT_import_unitypackage(Operator, ImportHelper):
    bl_idname = 'unitypackage_importer.import_unitypackage'
    bl_label = "Import from Unitypackage"
    bl_description = "Import one or more assets from scene(s) in .unitypackage file."

    # ImportHelper mixin settings
    filename_ext = '.unitypackage'
    filter_glob : StringProperty(default = '*.unitypackage', options = { 'HIDDEN' }, maxlen=255)

    # Import options
    import_mode : EnumProperty(
        name="Mode", description="How to import files from this .unitypackage file",
        items=(
            ('DIRECT', "Direct", "Will directly import individual assets from the file without resolving scenes / prefabs."),
            ('RESOLVED', "Resolved (WIP)", "Will resolve scenes and prefabs and import objects used within them while respecting existing relations.")
        ),
        default='DIRECT'
    )

    def draw(self, context):
        self.layout.label(text="Import Options")
        self.layout.prop(self, 'import_mode')

    def execute(self, context):
        # Call internal operator to handle import
        bpy.ops.unitypackage_importer.import_unitypackage_modal('INVOKE_DEFAULT', filepath=self.filepath, import_mode=self.import_mode)
        return { 'FINISHED' }


class UNITYPACKAGE_IMPORTER_OT_import_unitypackage_modal(Operator):
    bl_idname = 'unitypackage_importer.import_unitypackage_modal'
    bl_label = "Import from Unitypackage (Internal)"
    bl_description = "Internal operator for handling import from .unitypackage file with modal dialog to choose which assets to import."
    bl_options = { 'INTERNAL' } # Hide this operator from the operator search

    filepath : StringProperty()
    import_mode : StringProperty()

    def draw(self, context):
        self.layout.label(text="Select assets for import:")
        self.layout.template_list(
            'UNITYPACKAGE_IMPORTER_UL_import_list', "", 
            context.window_manager, 'unitypackage_importer_import_display_list', 
            context.window_manager, 'unitypackage_importer_import_display_list_index'
        )
        row = self.layout.row()
        row.operator("unitypackage_importer.select_all")
        row.operator("unitypackage_importer.deselect_all")

    def invoke(self, context, event):
        logger.info(f"Initiate import process for '{self.filepath}'...")

        # TODO: Invoke some sort of "indexing file" modal here indicating that the .unitypackage file is being indexed

        # Initialize parser for file
        self._parser = UnitypackageParser(filepath=self.filepath)
        
        if self.import_mode == 'DIRECT':
            # Direct import mode, just scan for all importable assets within archive
            prepare_direct_import(context, self._parser)

        elif self.import_mode == 'RESOLVED':
            # TODO: Resolved import mode, scan through all scenes / prefabs and find assets as they are implemented (keeping relations between them)
            prepare_resolved_import(context, self._parser)
        
        else:
            raise KeyError(self.import_mode)

        # Determine Initial Import List Item Visibility
        update_import_list(None, context)

        # Warp cursor is a hack to make the dialog appear in the center of the window
        context.window.cursor_warp(int(context.window.width / 2), int(context.window.height / 2))
        return context.window_manager.invoke_props_dialog(self, width=600)

    def execute(self, context):
        if self.import_mode == 'DIRECT':
            # Direct import mode, just scan for all importable assets within archive
            do_direct_import(context, self._parser)

        elif self.import_mode == 'RESOLVED':
            # TODO: Resolved import mode, scan through all scenes / prefabs and find assets as they are implemented (keeping relations between them)
            do_resolved_import(context, self._parser)

        # Close parser
        if self._parser:
            self._parser.close()

        return { 'FINISHED' }
    
    def cancel(self, context):
        # Close parser
        if self._parser:
            self._parser.close()
        
        print("Import aborted.")
        self.report({ 'INFO' }, "Import aborted.")


def add_test_items(context):
    import_list = context.window_manager.unitypackage_importer_import_list
    import_list.clear()

    item = import_list.add()
    item.name = "Mesh 1"
    item.icon = "MESH_DATA"
    item.is_selected = True
    item.is_expanded = True
    
    item = import_list.add()
    item.name = "Material 1"
    item.icon = "MATERIAL"
    item.is_selected = True
    item.indentation = 1
    
    item = import_list.add()
    item.name = "Texture 1"
    item.icon = "TEXTURE"
    item.is_selected = True
    item.indentation = 2
    
    item = import_list.add()
    item.name = "Texture 2"
    item.icon = "TEXTURE"
    item.is_selected = True
    item.indentation = 2
    
    item = import_list.add()
    item.name = "Texture 3"
    item.icon = "TEXTURE"
    item.is_selected = True
    item.indentation = 2
    
    item = import_list.add()
    item.name = "Material 2"
    item.icon = "MATERIAL"
    item.is_selected = True
    item.indentation = 1
    
    item = import_list.add()
    item.name = "Texture 1"
    item.icon = "TEXTURE"
    item.is_selected = True
    item.indentation = 2
    
    item = import_list.add()
    item.name = "Texture 2"
    item.icon = "TEXTURE"
    item.is_selected = True
    item.indentation = 2
    
    item = import_list.add()
    item.is_selected = True
    item.name = "Mesh 2"
    item.icon = "MESH_DATA"