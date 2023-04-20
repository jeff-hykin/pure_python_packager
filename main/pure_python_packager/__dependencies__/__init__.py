from os import remove, getcwd, makedirs, listdir, rename, rmdir, system
from os.path import isabs, isfile, isdir, join, dirname, basename, exists, splitext, relpath, join, dirname
from pathlib import Path
import glob
import os
import shutil
import sys
import warnings

# 
# helpers
# 
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

def make_relative_path(*, to, coming_from=None):
    if coming_from is None:
        coming_from = get_cwd()
    return os.path.relpath(to, coming_from)

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

def remove(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        try:
            os.remove(path)
        except:
            pass

# 
# globals
# 
this_file = make_absolute_path(__file__)
this_folder = dirname(this_file)
dependency_mapping_path = join(this_folder, '__dependency_mapping__.json')

# 
# find closest import path
#
*folders_to_this, _, _ = path_pieces(this_file)
best_match_amount = 0
best_import_zone_match = None
import sys
for each_import_path in sys.path:
    each_import_path = make_absolute_path(each_import_path)
    if not isdir(each_import_path):
        continue
    *folders_of_import_path, name, extension = path_pieces(each_import_path)
    folders_of_import_path = [ *folders_of_import_path, name+extension]
    matches = 0
    for folder_to_this, folder_to_some_import_zone in zip(folders_to_this, folders_of_import_path):
        if folder_to_this != folder_to_some_import_zone:
            break
        else:
            matches += 1
    
    if matches > best_match_amount:
        best_import_zone_match = each_import_path
        best_match_amount = matches

# shouldn't ever happen
if best_import_zone_match is None:
    raise Exception(f"""Couldn't find a path to {this_file} from any of {sys.path}""")

# 
# import json mapping
# 
import json
from os.path import join
# ensure it exists
if not isfile(dependency_mapping_path):
    with open(dependency_mapping_path, 'w') as the_file:
        the_file.write(str("{}"))
with open(dependency_mapping_path, 'r') as in_file:
    dependency_mapping = json.load(in_file)
    if not isinstance(dependency_mapping, dict):
        raise Exception(f"""\n\n\nThis file is corrupt (it should be a JSON object):{dependency_mapping_path}""")

# 
# calculate paths
# 
from random import random
counter = 0
import_strings = []
for dependency_name, dependency_info in dependency_mapping.items():
    counter += 1
    if dependency_name.startswith("__"):
        raise Exception(f"""dependency names cannot start with "__", but this one does: {dependency_name}. This source of that name is in: {dependency_mapping_path}""")
    
    target_path = join(this_folder, dependency_info["path"])
    relative_target_path = make_relative_path(to=target_path, coming_from=best_import_zone_match)
    # ensure the parent folder
    *path_parts, _, _ = path_pieces(join(relative_target_path, "_"))
    eval_part = dependency_info.get("eval", dependency_name)
    unique_name = f"{dependency_name}_{random()}_{counter}".replace(".","")
    target_folder_for_import = join(this_folder, dependency_name)
    if exists(target_folder_for_import):
        remove(target_folder_for_import)
    # symlink the folder
    Path(target_folder_for_import).symlink_to(dependency_info["path"])