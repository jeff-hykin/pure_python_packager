import sys
import os
from os.path import isabs, isfile, isdir, join, dirname, basename, exists, splitext, relpath
from os import remove, getcwd, makedirs, listdir, rename, rmdir, system
from pathlib import Path
from os.path import join, dirname
import warnings
import json

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

this_file = make_absolute_path(__file__)
this_folder = dirname(this_file)

path_to_original_dependency_initer = join(this_folder, "__dependencies__", "__init__.py")

content_of_original_dependency_initer = None
def get_original_dependency_initer():
    global content_of_original_dependency_initer
    if not content_of_original_dependency_initer:
        with open(path_to_original_dependency_initer,'r') as f:
            content_of_original_dependency_initer = f.read()
    else:
        return content_of_original_dependency_initer


# TODO: check git subrepo command        
def add_dependency(project_directory, url, module_name=None, module_path=None, extraction_eval=None):
    # detect module name
    if module_name == None:
        *folders, name, extension = path_pieces(url)
        module_name = name
    
    path_to_init = join(project_directory, "__dependencies__", "__init__.py")
    path_to_dependency_map = join(project_directory, "__dependencies__", "__dependency_mapping__.json")
    
    # create the __dependencies__/
    if not isdir(dirname(path_to_init)):
        os.makedirs(dirname(path_to_init), exist_ok=True)
    
    # create the __dependencies__/__init__.py
    if not isfile(path_to_init):
        with open(path_to_init, 'w') as the_file:
            the_file.write(get_original_dependency_initer())
    
    # create the __dependencies__/__dependency_mapping__.json
    if not isfile(path_to_dependency_map):
        with open(path_to_dependency_map, 'w') as the_file:
            the_file.write(str("{}"))
    with open(path_to_dependency_map, 'r') as in_file:
        dependency_mapping = json.load(in_file)
        if not isinstance(dependency_mapping, dict):
            raise Exception(f"""\n\n\nThis file is corrupt (it should be a JSON object):{path_to_dependency_map}""")
    
    # TODO: git subrepo clone
    
    # TODO: check the toml
    # if 

    # TODO: convert "from [self].thing1 import thing2" to "from .thing1 improt thing2"


