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
from time import time


def print_dict_recursive(data:dict, depth=0):
    pass


def format_dict_recursive(data:dict, depth=0):
    """
    Recursively prints a dictionary's key structure.
    
    """
    formatted = ""
    for key, value in data.items():
        if not key.startswith('_'):
            formatted += f"{'  - '*depth}{key}\n"
        if type(value) is dict:
            formatted += format_dict_recursive(value, depth + 1)
    
    return formatted


def timer(logger, condition=True):
    """
    Simple timing decorator to measure and log execution time of synchronous functions.

    """
    def decorator(f):
        if not condition:
            # Passthrough
            return lambda *args, **kwargs : f(*args, **kwargs)
        
        def wrapper(*args, **kwargs):
            t1 = time()
            result = f(*args, **kwargs)
            t2 = time()
            logger.debug(f"Function {f.__name__!r} took {(t2-t1):.4f}s")
            
            return result
        return wrapper
    return decorator
        