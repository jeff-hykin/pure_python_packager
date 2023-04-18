import sys
import os
from os.path import isabs, isfile, isdir, join, dirname, basename, exists, splitext, relpath
from os import remove, getcwd, makedirs, listdir, rename, rmdir, system
from pathlib import Path
from os.path import join, dirname
import warnings
  
def make_absolute_path(to, coming_from=None):
    # if coming from cwd, its easy
    if coming_from is None:
        return os.path.abspath(to)
    
    # source needs to be absolute
    coming_from_absolute = os.path.abspath(coming_from)
    # if other path is  absolute, make it relative to coming_from
    relative_path = to
    if os.path.isabs(to):
        relative_path = os.path.relpath(to, coming_from_absolute)
    return os.path.join(coming_from_absolute, relative_path)

this_file = make_absolute_path(__file__)
this_folder = dirname(this_file)
dependency_underscore_names = [ each for each in listdir(this_folder) if basename(each)[0:2] != '__' ] # ignore double-underscore names

def path_pieces(path):
    """
    example:
        *folders, file_name, file_extension = path_pieces("/this/is/a/filepath.txt")
    """
    folders = []
    while 1:
        path, folder = os.path.split(path)

        if folder != "":
            folders.append(folder)
        else:
            if path != "":
                folders.append(path)

            break
    folders.reverse()
    *folders, file = folders
    filename, file_extension = os.path.splitext(file)
    return [ *folders, filename, file_extension ]

# 
# find closest import path
#
*folders_to_this, _, _ = path_pieces(this_file)
best_match_amount = 0
best_import_zone_match = None
import sys
for each in sys.path:
    each = make_absolute_path(each)
    *folders, name, extension = path_pieces(each)
    folders = [ *folders, name+extension]
    matches = 0
    for folder_to_this, folder_to_some_import_zone in zip(folders_to_this, folders):
        if folder_to_this != folder_to_some_import_zone:
            break
        else:
            matches += 1
    
    if matches > best_match_amount:
        best_import_zone_match = each
        best_match_amount = matches

# shouldn't ever happen
if best_import_zone_match is None:
    raise Exception(f'''Couldn't find a path to {this_file} from any of {sys.path}''')


# 
# calculate path
# 
import_strings = []
for each in dependency_underscore_names:
    *folders, file_name, file_extension = path_pieces(join(this_folder, each))
    package_name = file_name+file_extension
    # NOTE: this is where the required structure of main/package_name exists
    path_parts = folders[best_match_amount:] + [ package_name, "main", package_name, ] 
    if os.path.isdir(join(best_import_zone_match, *path_parts)):
        if all(each.isidentifier() for each in path_parts):
            import_strings.append(f"import {'.'.join(path_parts)} as {package_name}")
        else:
            warnings.warn(f"There's a dependency path that contains a name that is not acceptable as an identifier:\npath parts: {path_parts}")
    else:
        warnings.warn(f"There's a dependency path but it doesnt have the right folder structure. This path isn't a folder: {join(*path_parts)}")

# 
# do the actual importing
#
import_string = "\n".join(import_strings)
try:
    exec(import_string)
except Exception as error:
    print(error)
    indented = import_string.replace('\n', '\n    ')
    print(f"Issue while trying to run the following:\n    {indented}")
    raise error