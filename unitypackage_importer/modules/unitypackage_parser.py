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
import os
import tarfile
import logging
from tarfile import TarFile, TarInfo
from typing import Union, List, Generator, Any
from ..config import log_level
from .tools import timer


logger = logging.getLogger("UnitypackageParser")
logger.setLevel(log_level)


class AssetEntry():
    _tarfile : TarFile
    _data : dict
    
    def __init__(self, tarfile : TarFile):
        self._data = {}
        self._tarfile = tarfile

    def set_value(self, key : str, value : Union[TarInfo, bytes, str]):
        """
        Sets attribute for the given key.
        Raises Exception if value is already set.
        Raises ValueError if value is empty or of unsupported type.

        """
        if key in self._data.keys(): 
            raise Exception(f"Attribute '{key}' already set!")
        if not value or type(value) not in [TarInfo, bytes, str]: 
            raise ValueError()

        self._data[key] = value

    def get_value(self, key : str) -> Union[bytes, str]:
        """
        Retrieves value for the given key.
        If the value isn't yet extracted, it will be replaced by the result of tf.extract(item).

        Note that extraction only happens once! After calling this function the value will either be
        of type bytes or str.
        
        """
        # Some quality of life pseudo-attributes
        if key == 'basename': 
            return os.path.basename(self.get_str_value('pathname'))
        if key == 'dirname':
            return os.path.dirname(self.get_str_value('pathname'))
        if key == 'extension': 
            return os.path.splitext(self.get_str_value('pathname'))[1]

        if not key in self._data.keys(): 
            raise KeyError(key)
        
        value = self._data[key]
        if type(value) == TarInfo:
            # Not yet extracted, extract first
            value = self._tarfile.extractfile(value).read()
            self._data[key] = value # Update value in dict
        
        return value

    def __getattr__(self, key : str) -> Any:
        """
        Will be invoked if attempting to access attribute that doesn't exist in module.
        If that happens, call get_value to allow accessing internal values as attributes.

        """
        return self.get_value(key)
    
    def get_str_value(self, key : str) -> str:
        """
        Retrieves the attribute value for the given key as a string.
        If the value is of type bytes, will return decoded string using text_encoding.
        Raises ValueError if value is neither of type bytes or str.

        See get_value for information about tar-file-extraction.

        """
        value = self.get_value(key)
        if type(value) not in [bytes, str]: 
            raise ValueError
        
        if type(value) == bytes:
            # Return string-decoded value
            return value.decode('utf-8')

        # Value is already a string, just return
        return value

    def has_keys(self, match_key : Union[str, List[str]]) -> bool:
        """
        Returns wether or not attributes with all of the specified names exist.

        """
        if type(match_key) == str:
            return match_key in self._data.keys()
        
        elif type(match_key) == list:
            return all([key in self._data for key in match_key ])
        
        raise TypeError()

    def __str__(self):
        if 'guid' in self._data.keys():
            return f"<AssetEntry instance (GUID: {self.get_value('guid')})>"
        
        return f"<AssetEntry instance>"


class UnitypackageParser():
    _filepath : str
    _tarfile : Union[TarFile, None]
    _asset_entries : Union[dict[str, AssetEntry], None]

    def __init__(self, filepath : str):
        self._filepath = filepath

        self._init_tarfile() # 1. load the tarfile
        self._init_asset_entries() # 2. Index the tarfile

    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        if not hasattr(self, '_tarfile'): return
        if not self._tarfile: return

        self._tarfile.close()

    @timer(logger)
    def _init_tarfile(self):
        if hasattr(self, '_tarfile'):
            raise Exception("Tarfile already initialized!")
        if not self._filepath:
            raise Exception("No filepath to unitypackage provided!")
        if not os.path.exists(self._filepath): 
            raise Exception(f"Provided file '{self._filepath}' does not exist!")
        if not tarfile.is_tarfile(self._filepath): 
            raise Exception(f"File '{self._filepath}' is not a tar archive! (Did you select a valid .unitypackage file?")
        
        logger.info(f"Opening file '{self._filepath}'...")
        self._tarfile = tarfile.open(self._filepath)

    @timer(logger)
    def _init_asset_entries(self):
        """
        Takes a .unitypackage tarfile and returns a dictionary of all assets,
        using the extracted pathname (utf-8 string) as the key and the tarinfo of the asset as the value.
        Only entries that contain a 'pathname' and an 'asset' attribute are included in the output dictionary.
        
        Note:
        I can't really add a progress indicator to this. The only way to know how many entries are in the tar
        archive is by iterating over them, at which point the majority of execution time has already passed,
        making a progress indicator afterwards meaningless.

        """
        if hasattr(self, '_asset_entries'):
            raise Exception("Asset entries already initialized!")
        if not hasattr(self, '_tarfile'):
            raise Exception("No tarfile! (Was _init_tarfile already called?)")

        self._asset_entries = {}
        logger.info("Indexing asset entries...")

        for tarinfo in self._tarfile:
            name_segments = tarinfo.name.split('/')
            name_segments_len = len(name_segments)
            if name_segments_len == 2:
                asset_entry : AssetEntry = self._asset_entries.setdefault(name_segments[0], AssetEntry(self._tarfile))
                if name_segments[1] == 'pathname':
                    # UTF-8 encoded text-file contining relative path of file in Unity's virtual file explorer
                    asset_entry.set_value('pathname', tarinfo) # Don't extract yet for performance, we will do that on-demand when (and if) we need to
                    asset_entry.set_value('guid', name_segments[0]) # Store GUID in dict too (We need to do it somewhere but only once, pathname exists for all items)
                
                elif name_segments[1] == 'asset':
                    # Asset or Unity Document, encoding varies on asset type 
                    asset_entry.set_value('asset', tarinfo) # Don't extract yet for performance, we will do that on-demand when (and if) we need to
                
                elif name_segments[1] == 'asset.meta':
                    # UTF-8 encoded text-file containing metadata for asset
                    asset_entry.set_value('asset_meta', tarinfo) # Don't extract yet for performance, we will do that on-demand when (and if) we need to
                
                elif name_segments[1] == 'preview.png':
                    # Preview image for Unity's virtual file explorer, we don't need this
                    # d['preview_image'] = tarfile
                    pass
                
                else:
                    # Something else that wasn't in my example files
                    logger.warn(f"Unknown key in asset entry: '{name_segments[1]}'!")
            
            elif name_segments_len > 2:
                # As far as I can tell .unitypackage tar-files will never exceed a depth of 2
                raise Exception(f"Path in tarinfo too deep! Expected up to 2 segments, got {len(name_segments)}! ('{tarinfo.name}')")

        # Filter out all entries that don't contain 'pathname' and 'asset' items
        self._asset_entries = { guid: entry for guid, entry in self._asset_entries.items() if entry.has_keys(['pathname', 'asset']) }
        
        logger.info(f"Done Indexing. {len(self._asset_entries)} relevant asset entries were found.")

    def get_asset_entries_by_extension(self, match_extension: Union[str, list[str]]) -> Generator[AssetEntry, None, None]:
        """
        Generator to return all assets from the .unitypackage matching a file extension.
        match_extension can be either a string or a list of string to match against multiple items.

        """
        if type(match_extension) == str:
            for asset_entry in self._asset_entries.values():
                if asset_entry.extension == match_extension:
                    yield asset_entry
        
        elif type(match_extension) == list:
            for asset_entry in self._asset_entries.values():
                if asset_entry.extension in match_extension:
                    yield asset_entry

        else:
            raise TypeError()
        
    def get_asset_entry_by_guid(self, guid : str) -> AssetEntry:
        """
        Retrieves an asset entry by its GUID.
        Raises keyerror if not found.

        """
        return self._asset_entries[guid]