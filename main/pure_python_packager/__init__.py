import sys
import os
from os.path import isabs, isfile, isdir, join, dirname, basename, exists, splitext, relpath
from os import remove, getcwd, makedirs, listdir, rename, rmdir, system
from pathlib import Path
from os.path import join, dirname
import warnings
import json
from .__dependencies__ import toml

default_indent = 4
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
def add_dependency(project_directory, url, commit_or_tag=None, module_name=None, module_path=None, extraction_eval=None):
    # TODO: try auto-detecting project_directory using cwd and pyproject.toml
    
    # FIXME: allow installing a specific tag
    
    *_, url_ending_name, _ = path_pieces(url)
    # detect module name
    if module_name == None:
        module_name = url_ending_name
    
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
    
    repo_path = f"{url_ending_name}_{hash(f"{commit_or_tag}{url}")}"
    
    # TODO: git subrepo clone
    # FIXME: checkout commit_or_tag
    
    if not module_path:
        main_module_path = None
        toml_path = join(repo_path, "pyproject.toml")
        if isfile(toml_path):
            toml_info = toml.load(toml_path)
            try:
                main_module_path = toml_info["tool"]["extra"]["main_module_path"]
            except Exception as error:
                pass
        if main_module_path == None:
            typical_module_path = join(repo_path, module_name)
            if isdir(typical_module_path) and isfile(join(repo_path, "setup.py")):
                print(f"guessing that: {typical_module_path} is source code folder within the repo")
                main_module_path = typical_module_path
        if main_module_path == None:
            raise Exception(f'''Please give a module_path argument, as I was unable to auto-detect the module path for {module_name}''')
    
    # 
    # update the dependency mapping
    # 
    dependency_mapping[module_name] = {
        "path": make_relative_path(to=main_module_path, coming_from=join(repo_path, "..")),
        "eval": extraction_eval or module_name,
    }
    with open(path_to_dependency_map, 'w') as outfile:
        json.dump(dependency_mapping, outfile, indent=default_indent)
            
    # TODO: convert "from [self].thing1 import thing2" to "from .thing1 improt thing2" within the repo

