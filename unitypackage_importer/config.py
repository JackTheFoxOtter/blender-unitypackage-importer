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
import logging

# Log level for loggers to use.
# Set to logging.DEBUG for development and logging.INFO for release version.
log_level = logging.DEBUG

# List of texture file extensions blender supports.
# See https://docs.blender.org/manual/en/latest/files/media/image_formats.html
texture_file_extensions = [
    '.bmp',                # BMP
    '.sgi', '.rgb', '.bw', # Iris
    '.png',                # PNG
    '.jpg', '.jpeg',       # JPEG
    '.jp2', '.j2c',        # JPEG 2000
    '.tga',                # Targa
    '.cin', '.dpx',        # Cineon & DPX
    '.exr',                # OpenEXR
    '.hdr',                # Radiance HDR
    '.tif', '.tiff',       # TIFF
    '.webp'                # WebP
]

# List of supported model formats that can be imported.
model_file_extensions = [
    '.fbx', '.glb', '.gltf'
]