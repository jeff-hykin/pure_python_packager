from __future__ import absolute_import

from os import remove, getcwd, makedirs, listdir, rename, rmdir, system
from os.path import isabs, isfile, isdir, join, dirname, basename, exists, splitext, relpath, join, dirname
from pathlib import Path
import glob
import os
import shutil
import sys
import warnings
starting_globals = dict(globals())

# 
# helpers
# 
from hashlib import md5 

def consistent_hash(value):
    if isinstance(value, bytes):
        return md5(value).hexdigest()
    
    if isinstance(value, str):
        return md5(("@"+value).encode('utf-8')).hexdigest()
    
    if isinstance(value, (bool, int, float, type(None))):
        return md5(str(value).encode('utf-8')).hexdigest()
        
    else:
        return md5(pickle.dumps(value, protocol=4)).hexdigest()

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
    if not Path(path).is_symlink() and os.path.isdir(path):
        shutil.rmtree(path)
    else:
        try:
            os.remove(path)
        except:
            pass

def final_target_of(path):
    # resolve symlinks
    if os.path.islink(path):
        have_seen = set()
        while os.path.islink(path):
            path = os.readlink(path)
            if path in have_seen:
                return None # circular broken link
            have_seen.add(path)
    return path
    
# 
# globals
# 
this_file = make_absolute_path(__file__)
this_folder = dirname(this_file)
settings_path = join(this_folder, '..', 'settings.json')

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
if not isfile(settings_path):
    with open(settings_path, 'w') as the_file:
        the_file.write(str("{}"))
with open(settings_path, 'r') as in_file:
    settings = json.load(in_file)
    if not isinstance(settings, dict):
        raise Exception(f"""\n\n\nThis file is corrupt (it should be a JSON object):{settings_path}""")

# ensure that pure_python_packages exists
if not isinstance(settings.get("pure_python_packages", None), dict):
    settings["pure_python_packages"] = {}
dependency_mapping = settings["pure_python_packages"]

# 
# calculate paths
# 
from random import random
counter = 0
import_strings = []
for dependency_name, dependency_info in dependency_mapping.items():
    counter += 1
    if dependency_name.startswith("__"):
        raise Exception(f"""dependency names cannot start with "__", but this one does: {dependency_name}. This source of that name is in: {settings_path}""")
    
    target_path = join(this_folder, dependency_info["path"])
    relative_target_path = make_relative_path(to=target_path, coming_from=best_import_zone_match)
    # ensure the parent folder
    *path_parts, _, _ = path_pieces(join(relative_target_path, "_"))
    eval_part = dependency_info.get("eval", dependency_name)
    unique_name = f"{dependency_name}_{random()}_{counter}".replace(".","")
    target_folder_for_import = join(this_folder, dependency_name)
    if not Path(target_folder_for_import).is_symlink() or final_target_of(target_folder_for_import) != dependency_info["path"]:
        # clear the way
        remove(target_folder_for_import)
        # symlink the folder
        Path(target_folder_for_import).symlink_to(dependency_info["path"])

# 
# python-include
# 


import sys
import os
import inspect
import textwrap
import importlib
from os.path import isabs, isfile, isdir, join, dirname, basename, exists, splitext, relpath, abspath, normpath


ModuleClass = type(sys)
dont_override = ( '__name__', '__doc__', '__package__', '__loader__', '__spec__', '__annotations__', '__builtins__', '__file__', )

___included_modules___ = {}
___link_to_real_system_path___ = sys.path
class HackySystemPathList(list):
    @property
    def __iter__(self,):
        # return the injected list
        output = super().__iter__
        # but replace this hacky list with the actual normal path list after it is called 1 time
        sys.path = ___link_to_real_system_path___
        return output

def file(path, globals=None):
    """
        Examples:
            import python_inlcude
            hello = python_inlcude.file("./path/to/file/with/hello/func/code.py", {"__file__":__file__}).hello
            # import [*everything*] from-anywhere (does pollute global namespace)
            python_inlcude.file("./path/to/file/with/hello/func/code.py", globals())
        Summary:
            Use a relative or absolute path to import all of the globals from that file into the current file
            This will not run code more than once, even if it is included multiple times
    """
    global ___link_to_real_system_path___
    global ___included_modules___
    your_globals = globals
    absolute_import_path = None
    is_absolute_path = isabs(path)
    if is_absolute_path:
        absolute_import_path = path
    else:
        parent_path = None
        the_filepath_was_in_globals = type(your_globals) == dict and type(your_globals.get("__file__", None)) == str
        # if they provide a path
        if the_filepath_was_in_globals:
            parent_path = dirname(your_globals['__file__'])
        # if this is being run inside a repl, use cwd
        elif sys.path[0] == '':
            parent_path = os.getcwd()
        # try to get it from inspect
        else:
            upstack = 1
            caller_relative_filepath = inspect.stack()[upstack][1]
            parent_path = dirname(abspath(caller_relative_filepath))
        
        absolute_import_path = join(parent_path, path)
    
    # normalize before using
    absolute_import_path = abspath(normpath(absolute_import_path))
    
    # ensure this is a dict
    your_globals = your_globals if type(your_globals) == dict else {}
    
    #
    # error handling
    #
    if not exists(absolute_import_path):
        if is_absolute_path:
            raise Exception(textwrap.dedent('''
            
            
            in: include.file("'''+path+'''")
            I don't see a file for that path, which I believe is an absolute file path
            '''))
        else:
            header = textwrap.dedent('''
                
                in: include.file("'''+path+'''")
                I don't see a file for that path, however
                - I think that is a relative path
            ''')
            
            if the_filepath_was_in_globals:
                source_of_parent = ""
                raise Exception(header+textwrap.dedent('''
                - I found a '__file__' key in the globals argument, e.g. include.file(path, globals)
                - I used that __file__ to resolve the path to get the absolute path
                - the resolved absolute path was this: "'''+absolute_import_path+'''"
                - that is where I couldn't find a file
                '''))
            else:
                raise Exception(header+textwrap.dedent('''
                - I didn't see a str value for '__file__' in the globals argument, e.g. include.file(path, globals)
                - So instead I tried finding your directory by searching up the inspect path
                - the resolved absolute path was this: "'''+absolute_import_path+'''"
                - that is where I couldn't find a file
                '''))
    
    # if the module was cached
    if absolute_import_path in ___included_modules___ and type(___included_modules___) == ModuleClass:
        module_as_dict = ___included_modules___[absolute_import_path]
    else:
        # FIXME: check for periods in the filename, as they will (proabably) be interpeted as sub-module attributes and break the import
        # get the python file name without the extension
        filename, file_extension = os.path.splitext(basename(absolute_import_path))
        # add a wrapper to the sys path, because modifying it directly would cause polltion/side effects
        # this allows us to import the module from that absolute_import_path 
        # this hacked list will reset itself immediately after the desired file is imported
        ___link_to_real_system_path___ = sys.path
        sys.path = HackySystemPathList([ dirname(absolute_import_path) ])
        
        # make room for the new module
        module_before_replacement = None
        if filename in sys.modules:
            module_before_replacement = sys.modules[filename]
            del sys.modules[filename]
            
        # import the actual module
        module = importlib.import_module(filename)
        module_as_dict = vars(module)
        # save the module to be in our cache
        ___included_modules___[absolute_import_path] = module_as_dict
        # restore the old module if there was one
        if module_before_replacement:
            sys.modules[filename] = module_before_replacement
        else:
            # don't save included modules on the sys.modules at all
            del sys.modules[filename]
    
    # cram the new module into your_globals
    for each in module_as_dict:
        if each not in dont_override:
            your_globals[each] = module_as_dict[each]
    
    return module

for dependency_name, dependency_info in dependency_mapping.items():
    # need to change the module name to make it unique before importing
    path_to_dependency = join(this_folder, dependency_name)
    unqiue_name = f"{dependency_name}___{consistent_hash(path_to_dependency)}"
    os.makedirs(join(this_folder, "__name_mapping__"), exist_ok=True)
    path_with_unique_name = join(this_folder, "__name_mapping__", unqiue_name)
    relative_target_path = join("..", dependency_info["path"])
    # make sure the symlink exists
    if not Path(path_with_unique_name).is_symlink() or final_target_of(path_with_unique_name) != relative_target_path:
        # clear the way
        remove(path_with_unique_name)
        # symlink the folder
        Path(path_with_unique_name).symlink_to(relative_target_path)
    exec(f"{dependency_name} = file(path_with_unique_name)")
