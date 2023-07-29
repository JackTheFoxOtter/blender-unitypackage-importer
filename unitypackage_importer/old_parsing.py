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

# from tarfile import TarInfo
# from os.path import dirname, basename, isfile, isdir, join
# from unityparser import UnityDocument
# from unityparser.utils import load_all
# from unityparser.register import UnityScalarRegister

# from .config import mesh_file_extensions, texture_file_extensions
# from .modules.tools import timer
# from .modules.logging import get_logger


# logger = get_logger("Old Parsing")


# @timer(logger=logger)
# def get_asset_entries(tf):
#     """
#     Takes a .unitypackage tarfile and returns a dictionary of all assets,
#     using the extracted pathname (utf-8 string) as the key and the tarinfo of the asset as the value.
#     Only entries that contain a 'pathname' and an 'asset' attribute are included in the output dictionary.
    
#     """
#     asset_entries = {}
    
#     for tarinfo in tf:
#         name_segments = tarinfo.name.split('/')
#         name_segments_len = len(name_segments)
#         if name_segments_len == 2:
#             entry = asset_entries.setdefault(name_segments[0], {})
#             if name_segments[1] == 'pathname':
#                 # UTF-8 encoded text-file contining relative path of file in Unity's virtual file explorer
#                 entry['pathname'] = tf.extractfile(tarinfo).read().decode('utf-8') # Always extract and decode pathname, needed for every entry
#                 entry['guid'] = name_segments[0] # Store GUID in dict too (We need to do it somewhere but only once, pathname exists for all items)
#             elif name_segments[1] == 'asset':
#                 # Asset or Unity Document, encoding varies on asset type 
#                 entry['asset'] = tarinfo # Don't extract yet for performance, we will do that on-demand when (and if) we need to
#             elif name_segments[1] == 'asset.meta':
#                 # UTF-8 encoded text-file containing metadata for asset
#                 entry['asset_meta'] = tarinfo # Don't extract yet for performance, we will do that on-demand when (and if) we need to
#             elif name_segments[1] == 'preview.png':
#                 # Preview image for Unity's virtual file explorer, we don't need this
#                 # d['preview_image'] = tarfile
#                 pass
#             else:
#                 # Something else that wasn't in my example files
#                 logger.info(f"Unknown key in asset entry: '{name_segments[1]}'!")
        
#         elif name_segments_len > 2:
#             # As far as I can tell .unitypackage tar-files will never exceed a depth of 2
#             raise Exception(f"Path in tarinfo too deep! Expected up to 2 segments, got {len(name_segments)}! ('{tarinfo.name}')")
            
#     return { guid: entry for guid, entry in asset_entries.items() if {'pathname', 'asset'} <= entry.keys() } # Filter out all entries that don't contain 'pathname' and 'asset' items


# @timer(logger=logger)
# def get_or_extract(tf, asset_entry, key, decode_as_text=False, text_encoding='utf-8'):
#     """
#     Retrieves an item from an asset entry dictionary.
#     If the item isn't yet extracted, it be replaced by the result of tf.extract(item).
#     This is determined using the item '<key>_extracted', interpreted as boolean value.
    
#     """
#     if type(asset_entry[key]) == TarInfo:
#         # Not yet extracted, extract first
#         asset_entry[key] = tf.extractfile(asset_entry[key])
        
#         if decode_as_text:
#             # Decode extracted item as text using specified encoding
#             asset_entry[key] = asset_entry[key].read().decode(text_encoding)
        
#     return asset_entry[key]


# @timer(logger=logger)
# def load_unity_document(tf, asset_entry):
#     """
#     Creates a UnityDocument object from yaml data extracted from the provided tarfile / fileinfo.
#     Basically just the same as UnityDocument.load_yaml(self, file_path=None), just that we can do it in-memory.
    
#     """
#     register = UnityScalarRegister()
#     asset_file = get_or_extract(tf, asset_entry, 'asset', True)
#     data = [d for d in load_all(asset_file, register)] # TODO load_all takes a SIGNIFICANT amount of time! Custom YAML-parser optimized for our use-case would tremendously speed this up.
#     return UnityDocument(data, newline='\n', register=register)


# @timer(logger=logger)
# def get_material_details(tf, asset_entries, material_entry, fileID):
#     """
#     Retrieves information about a material described through a unity .mat file.
#     Information contains shader as well as textures and a best guess as to what purpose each texture holds.
#     Returns a dict with the following information:
#     {
#         'original_material_name': <Original Material Name>,
#         'original_shader_name': <Original Shader Name>,
#         'determined_material_type': <'TOON', 'PBRS', 'PBRM', [...]>,
#         'textures': [
#             {
#                 'original_input_name': <Original Names of Input Sockets this texture has been used in>,
#                 'original_texture_name': <Original Texture Name>,
#                 'determined_texture_type': <'ALBEDO', 'METALLICNESS', 'BUMP', [...]>,
#                 'scale': { x: <Scale X>, y: <Scale Y> },
#                 'offset': { x: <Offset X>, y: <Offset Y> },
#                 'texture_entry': <Asset entry of texture>
#             }
#         ]
#     }
    
#     """
#     material_doc = load_unity_document(tf, material_entry)
#     material_doc_entry = next(entry for entry in material_doc.entries if entry.anchor == str(fileID))
    
#     material_details = {}
#     material_details['original_material_name'] = material_doc_entry.__dict__['m_Name']
#     material_details['original_shader_name'] = material_doc_entry.__dict__['stringTagMap']['OriginalShader'] # TODO: Unreliable, might be incorrect / outdated if shader changed!
#     # TODO: Shader may or may not exist in .unitypackage. Look for it anyway to get the most up-to-date values
#     material_details['determined_material_type'] = 'UNKNOWN' # TODO Heuristic to figure this out!
    
#     textures = []
#     for texture_dict in material_doc_entry.__dict__['m_SavedProperties']['m_TexEnvs']:
#         key, value = next(iter(texture_dict.items())) # Always dictionary with 1 item
#         if value['m_Texture'] != {'fileID': 0}:
#             # Every non-empty texture input of material
#             # TODO: I *think* this can contain textures / inputs that don't belong to the current shader if the shader changed!
#             fileID, guid, type = value['m_Texture'].values() # Points to internal or external texture file
#             if texture_entry := asset_entries.get(guid, None):
#                 if texture_entry['pathname'].endswith(texture_file_extensions):
#                     texture_details = {}
#                     texture_details['original_input_name'] = key
#                     texture_details['original_texture_name'] = texture_entry['pathname']
#                     texture_details['determined_texture_type'] = 'UNKNOWN' # TODO Heuristic to figure this out!
#                     texture_details['scale'] = value['m_Scale']
#                     texture_details['offset'] = value['m_Offset']
#                     texture_details['texture_entry'] = texture_entry
#                     textures.append(texture_details)
    
#     material_details['textures'] = textures
        
#     return material_details


# @timer(logger=logger)
# def find_models_in_unity_document(tf, asset_entries, asset_entry, recursive=False):
#     """
#     For a given unity document (scene or prefab), find models (mesh + textures) referenced within.
#     We achieve this by searching the prodivded tarinfo for PrefabInstances which point to a model file.
#     Currently, this is determined by the file extension of the prefab's target entry's pathname.
    
#     """
#     doc = load_unity_document(tf, asset_entry)
#     for doc_entry in doc.entries:
#         if doc_entry.__class__.__name__ == 'PrefabInstance':
#             if child_asset_entry := asset_entries.get(doc_entry.m_SourcePrefab['guid'], None):
#                 if recursive and child_asset_entry['pathname'].endswith('.prefab'):
#                     # Source Prefab is parseable file, resolve recursively
#                     yield from find_models_in_unity_document(tf, asset_entries, child_asset_entry, recursive)
                
#                 elif child_asset_entry['pathname'].endswith(mesh_file_extensions):
#                     # Entry is an asset prefab pointing to an asset with a mesh file extension, determine materials used and yield
#                     materials = []
#                     modifications = doc_entry.__dict__['m_Modification']['m_Modifications']
#                     material_overrides = filter(lambda x: x['propertyPath'].startswith('m_Materials.Array.data'), modifications)
#                     for material_override in sorted(material_overrides, key=lambda x: x['propertyPath']):
#                         fileID, guid, type = material_override['objectReference'].values() # Points at material entry used for this override (material slot)
#                         material_entry = asset_entries[guid]
#                         if material_entry['pathname'].endswith('.mat'):
#                             materials.append(get_material_details(tf, asset_entries, material_entry, fileID))
                    
#                     # print(materials)
#                     yield (child_asset_entry['pathname'], child_asset_entry, materials)


# @timer(logger=logger)
# def resolve_asset_entries(tf, asset_entries):
#     """
#     First, scan the asset entries for .unity (scene) files and parse them.
#     Then, apply heuristic to those to find all assets (meshes and textures) that can be exported.
    
#     """
#     object_data = {} # {Avatar1Name: {meshes: <Meshes>, textures: <Textures>}, ...}
    
#     for asset_entry in asset_entries.values():
#         # print(asset_entry['pathname'])

#         if not (asset_entry['pathname'].endswith('.unity') or asset_entry['pathname'].endswith('.prefab')):
#             # Continue, not a scene or prefab
#             continue

#         logger.info(f"Scanning scene / prefab '{basename(asset_entry['pathname'])}' for models... ({asset_entry['guid']})")
        
#         if model_infos := find_models_in_unity_document(tf, asset_entries, asset_entry, True):
#             for name, mesh_entry, materials in model_infos:
#                 logger.info(f"  - (Mesh) '{name}'")
#                 for material_details in materials:
#                     logger.info(f"      - (Material) '{material_details['original_material_name']}'")
#                     for texture_details in material_details['textures']:
#                         logger.info(f"          - (Texture) '{texture_details['original_texture_name']}'")
#         else:
#             logger.info(f"No models found!")
            
#         # break # Break after first scene for testing
    
#     return object_data