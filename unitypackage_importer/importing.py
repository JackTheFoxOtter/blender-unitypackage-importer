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
import io
import os
import bpy
import logging
from pathlib import PurePosixPath
from .config import log_level, texture_file_extensions, model_file_extensions
from .modules.unitypackage_parser import UnitypackageParser, AssetEntry
from .modules.tools import timer


# TODO: This could probably significantly speed up if we can skip creating temporary files on disk, but I so far haven't figured out how to implement that.
#       Even if just for textures that would be a pretty significant performance improvement.


logger = logging.getLogger("Unitypackage Asset Importer")
logger.setLevel(log_level)


# Create session temp directory.
# This is based off of Blender's temp dir which is cleared after the session.
plugin_temp_dir = os.path.join(bpy.app.tempdir, 'unitypackage_importer_temp')
if not os.path.exists(plugin_temp_dir):
    os.makedirs(plugin_temp_dir)


class TempFile():
    """
    Temporary file on the file system to invoke Blender's importers.
    Can (and should!) be used as a context manager, the file will be deleted once the context manager is exited.

    """
    fullpath : str

    def __init__(self, basename : str, data : bytes):
        self.fullpath = os.path.join(plugin_temp_dir, basename)
        logger.debug(f"Creating temporary file '{self.fullpath}' and writing {len(data)} bytes...")
        with open(self.fullpath, 'wb') as f:
            f.write(data)

    def __enter__(self):
        return self.fullpath

    def __exit__(self, type, value, traceback):
        # Clean up afterwards
        os.remove(self.fullpath)


def _add_import_item(import_list, guid : str, name : str, icon : str = 'NONE', is_selected=True, is_expanded=True, indentation=0):
    import_item = import_list.add()
    import_item.guid = guid
    import_item.name = name
    import_item.icon = icon
    import_item.is_selected = is_selected
    import_item.is_expanded = is_expanded
    import_item.indentation = indentation

@timer(logger)
def prepare_direct_import(context, parser : UnitypackageParser):
    import_list = context.window_manager.unitypackage_importer_import_list
    import_list.clear()

    # Get importable assets from .unitypackage
    texture_asset_infos = [ (asset_entry.dirname, asset_entry.basename, 'Texture', asset_entry) for asset_entry in parser.get_asset_entries_by_extension(texture_file_extensions) ]
    model_asset_infos = [ (asset_entry.dirname, asset_entry.basename, 'Model', asset_entry) for asset_entry in parser.get_asset_entries_by_extension(model_file_extensions) ]
    asset_infos = texture_asset_infos + model_asset_infos
    
    # Initialize progress indicator
    context.window_manager.progress_begin(0, len(asset_infos))
    
    # Sort for alphabetic ordering (and correct display of folder hierachy)
    asset_infos.sort(key=lambda e: (e[0], e[1]))
    
    # Populate list with heirachy
    prev_directories = []
    for index, (dirname, basename, asset_type, asset_entry) in enumerate(asset_infos):
        # Build directory tree
        directories = PurePosixPath(dirname).parts
        hierachy_changed = False
        for index, directory in enumerate(directories):
            if hierachy_changed or index >= len(prev_directories) or prev_directories[index] != directory:
                hierachy_changed = True
                _add_import_item(import_list, '', directory, 'FILE_FOLDER', indentation=index)
        prev_directories = directories

        # Add asset node
        if asset_type == 'Texture':
            _add_import_item(import_list, asset_entry.guid, basename, 'TEXTURE', indentation=len(directories))
        elif asset_type == 'Model':
            _add_import_item(import_list, asset_entry.guid, basename, 'MESH_DATA', indentation=len(directories))
        
        # Update progress indicator
        context.window_manager.progress_update(index + 1)

    # End progress indicator
    context.window_manager.progress_end()


@timer(logger)
def do_direct_import(context, parser : UnitypackageParser):
    full_import_list = context.window_manager.unitypackage_importer_import_list
    import_list = [ item for item in full_import_list if all([ item.is_selected, item.is_enabled, item.guid ]) ]

    # TODO: This takes too long, windows gets in the way.
    # TODO: We need a second kind of progress indicator that actually refreshes the window to prevent
    # TODO: Windows from flagging it as non-responsive after 5 seconds!
    # (Operator window stays open during this, perhaps progress bar like https://blender.stackexchange.com/a/231693/89047 ?)

    # Initialize progress indicator
    context.window_manager.progress_begin(0, len(import_list))

    for index, import_item in enumerate(import_list):
        asset_entry : AssetEntry = parser.get_asset_entry_by_guid(import_item.guid)
        if asset_entry.extension in texture_file_extensions:
            with TempFile(asset_entry.basename, asset_entry.asset) as temp_file_path:
                image = bpy.data.images.load(temp_file_path)
                image.pack()

        # Update progress indicator
        context.window_manager.progress_update(index + 1)
    
    # End progress indicator
    context.window_manager.progress_end()
        


def prepare_resolved_import(context, parser : UnitypackageParser):
    raise NotImplementedError()


def do_resolved_import(context, parser : UnitypackageParser):
    raise NotImplementedError()