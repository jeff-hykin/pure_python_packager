import os
from collections import namedtuple
import json
import re

from .__dependencies__.walk_up import walk_up_until
from .__dependencies__.super_map import Map, LazyDict
from .__dependencies__ import ez_yaml

def find_and_load(file_name, *, fully_parse_args=False, parse_args=False, args=None, defaults_for_local_data=[], cd_to_filepath=True, show_help_for_no_args=False):
    """
        Example Python:
            # basic call
            config, path_to, *_ = find_and_load("info.yaml", defaults_for_local_data=["DEV"])
            # full call
            info = find_and_load("info.yaml", defaults_for_local_data=["DEV"], cd_to_filepath=True)
            # parse args from sys.argv (everything after "--")
            info = find_and_load("info.yaml", parse_args=True)
        
        Returns:
            info.config         # the resulting dictionary for all the selected options
            info.path_to            # a dictionary of paths relative to the root_path
            info.absolute_path_to   # same dictionary of paths, but made absolute
            info.unused_args        # all args before a '--' argument
            info.secrets            # (secrets) from the local data file
            info.available_profiles      # the dictionary of all possible options
            info.selected_profiles  # the dictionary of the local config-choices files
            info.root_path          # parent folder of the .yaml file
            info.project            # the dictionary to everything inside (project)
            info.local_data         # the local_data file as a dictionary
            info.as_dict            # the dictionary to the whole file (info.yaml)
        
        Example Yaml File:
            (project):
                # paths the code will probably need to use
                (path_to):
                    project_root: "./"
                
                # this is your local-machine config choices
                # (should point to a file that is git-ignored)
                # (this file will be auto-generated with the correct format)
                (local_data): ./local_data.ignore.yaml
                
                # below are options that the config file can choose
                #     when multiple options are selected
                #     their keys/values will be merged recursively
                (profiles):
                    (default):
                        mode: development
                        constants:
                            pi: 3 # pi is 'bout 3 
                    OPTION1:
                        mode: blah blah blah
                    
                    OPTION2:
                        mode: blah2 blah2 blah2
                    
                    OPTION3: !load_yaml_file ./options/opt3.yaml
    """
    if fully_parse_args:
        parse_args = True
    
    # 
    # load the yaml
    # 
    if True:
        path = walk_up_until(file_name)
        if path == None:
            raise Exception(f'''\n\nThis is an error while trying to load your local_data file\nI started inside this folder: {os.getcwd()}\nthen I looked for this file: {file_name}\nI checked all the parent folders too and I was unable to find that file.\n\nToDo: Please create that file or possibly run your command from a different directory''')
        root_path = FS.dirname(path)
        if cd_to_filepath: os.chdir(root_path)
        info = ez_yaml.to_object(file_path=path, load_nested_yaml=True)
        project = info.get("(project)", {})
        # TODO: add error if missing

    # 
    # load PATHS
    # 
    if True:
        def make_absolute_root_path(path_string):
            *folders, name, ext = FS.path_pieces(path_string)
            # if there are no folders then it must be a relative path (otherwise it would start with the roo "/" folder)
            if len(folders) == 0:
                folders.append(".")
            # if not absolute, then make it absolute
            if folders[0] != "/":
                if folders[0] == '.' or folders[0] == './':
                    _, *folders = folders
                return FS.absolute_path(FS.join(root_path, path_string))
            return path_string
        def make_relative_path(path_string):
            absolute_path = make_absolute_root_path(path_string)
            return os.path.relpath(absolute_path, root_path)
        
        def recursive_convert(a_dict):
            relative_paths = LazyDict()
            absolute_paths = LazyDict()
            for each_key, each_value in a_dict.items():
                if isinstance(each_value, dict):
                    relative_paths[each_key], absolute_paths[each_key] = recursive_convert(each_value)
                else:
                    relative_paths[each_key], absolute_paths[each_key] = make_relative_path(str(each_value)), make_absolute_root_path(str(each_value))
            return relative_paths, absolute_paths
        
        path_to, absolute_path_to = recursive_convert(project.get("(path_to)", {}))
    
    # 
    # 
    # find selected local_data profiles
    # 
    # 
    if True:
        local_data         = None
        selected_profiles  = None
        local_secrets      = {"example": "key29i5805"}
        local_data_path    = project.get("(local_data)", None)
        available_profiles = project.get("(profiles)", {})
        help_structure     = project.get("(help)", None)
        
        # handle the (inherit)
        available_profiles = resolve_profiles(available_profiles, path)
        
        if local_data_path:
            try:
                local_data = ez_yaml.to_object(file_path=local_data_path)
                selected_profiles = local_data.get("(selected_profiles)", [])
                local_secrets     = local_data.get("(secrets)"          , {})
            except Exception as error:
                pass
        # create the default options file if it doesnt exist, but path does
        for each_option in defaults_for_local_data:
            if each_option not in available_profiles:
                raise Exception(f"""
                
                    ---------------------------------------------------------------------------------
                    When calling: find_and_load("{path}", defaults_for_local_data= *a list* )
                    `defaults_for_local_data` contained this option: {each_option}
                    
                    However, your info file: {path}
                    only has these options: {list(available_profiles.keys())}
                    Inside that file, look for "(project)" -> "(profiles)" -> *option*,
                    
                    LIKELY SOLUTION:
                        Remove {each_option} from the `defaults_for_local_data` in your python file
                    
                    ALTERNATIVE SOLUTIONS:
                        - Fix a misspelling of the option
                        - Add {each_option} to "(profiles)" in {path}
                    ---------------------------------------------------------------------------------
                """.replace("\n                ", "\n"))
        if selected_profiles is None:
            if not isinstance(local_data_path, str):
                selected_profiles = []
                local_secrets = {}
            else:
                FS.create_folder(FS.dirname(local_data_path))
                ez_yaml.to_file(
                    file_path=local_data_path,
                    obj={
                        "(selected_profiles)": defaults_for_local_data,
                        "(secrets)": local_secrets,
                    },
                )
                selected_profiles = list(defaults_for_local_data)
                local_data = { "(selected_profiles)" : selected_profiles }
        selected_profiles = reversed(selected_profiles) # this makes first===highest priority 
        config = available_profiles.get("(default)", {})
    
    # 
    # parse cli arguments
    #
    if True:
        import sys
        direct_args = args != None
        looking_for_double_dash = parse_args and not direct_args
        
        command_prefix = f'python {sys.argv[0]} '
        if looking_for_double_dash:
            command_prefix += "-- "
        
        if parse_args and args is None:
            args = list(sys.argv)
            args.pop(0) # remove the path of the python file
        
        if args is None:
            args = []
        
        # 
        # remove up to the first "--" argument and only until the next "--" argument
        # 
        unused_args = []
        remaining_args = list(args)
        if looking_for_double_dash:
            while len(remaining_args) > 0:
                if remaining_args[0] == '--':
                    remaining_args.pop(0)
                    break
                unused_args.append(remaining_args.pop(0))
        resume_unused = False
        second_half_unused = list(remaining_args)
        new_remaining_args = []
        for each in list(second_half_unused):
            if each != "--":
                new_remaining_args.append(each)
                second_half_unused.pop(-1)
            else:
                break
        unused_args += second_half_unused
        remaining_args = list(new_remaining_args)
        
        
        # 
        # find --help
        # 
        args_after_help = []
        has_help_arg = False
        for each_arg in remaining_args:
            if has_help_arg:
                args_after_help.append(each_arg)
            elif each_arg == "--help":
                has_help_arg = True
        if has_help_arg or (show_help_for_no_args and len(args) == 0):
            top_level_options = "- "+("\n                    - ").join(list(config.keys()))
            default_profiles  = "- "+("\n                    - ").join(list(selected_profiles))
            quik_config_help = f"""
                
                ---------------------------------------------------------------------------------
                QUIK CONFIG HELP
                ---------------------------------------------------------------------------------
                
                open the file below and look for "(profiles)" for more information:
                    {path}
                
                examples:
                    {command_prefix} --help --profiles
                    {command_prefix} --help key1
                    {command_prefix} --help key1:sub_key
                    {command_prefix} --help key1:sub_key key2
                    {command_prefix} thing1:"Im a new value"          part2:"10000"
                    {command_prefix} thing1:"I : cause errors"        part2:10000
                    {command_prefix} 'thing1:"I : dont cause errors"  part2:10000
                    {command_prefix} 'thing1:["Im in a list"]'
                    {command_prefix} 'thing1:part_a:"Im nested"'
                
                how it works:
                    - given "thing1:10", "thing1" is the key, "10" is the value
                    - All values are parsed as json/yaml
                        - "true" is boolean true
                        - "10" is a number
                        - '"10"' is a string (JSON escaping)
                        - '"10\\n"' is a string with a newline
                        - '[10,11,hello]' is a list with two numbers and an unquoted string
                        - '{'{"thing": 10}'}' is a map/object
                        - "blah blah" is an un-quoted string with a space. Yes its valid YAML
                        - multiline values are valid, you can dump an whole JSON doc as 1 arg
                    - "thing1:10" overrides the "thing1" in the (profiles) of the info.yaml
                    - "thing:subThing:10" is shorthand, 10 is the value, the others are keys
                      it will only override the subThing (and will create it if necessary)
                    - '{'{"thing": {"subThing":10} }'}' is long-hand for "thing:subThing:10"
                    - '"thing:subThing":10' will currently not work for shorthand (parse error)
                
                options:
                    --help
                    --profiles
                
                ---------------------------------------------------------------------------------
                
                your default top-level keys:
                    {top_level_options}
                your local defaults file:
                    {local_data_path}
                your default profiles:
                    {default_profiles}
                
                ---------------------------------------------------------------------------------
            
            """.replace("\n            ", "\n")
            
            # 
            # check for user-provided help
            # 
            if len(args_after_help) > 0:
                if args_after_help[0] == "--profiles":
                    args_after_help.pop(0) # remove the "--profiles" arg
                    
                    available_profile_names = list(available_profiles.keys())
                    available_profile_names = [ each for each in available_profile_names if each != '(default)']
                    # if that was the only arg
                    if len(args_after_help) == 0:
                        if len(available_profiles) == 0:
                            print(f"I don't see any available profiles")
                            print(f"If that is strange, open up {path} and look for (profiles):")
                            print(f"See https://github.com/jeff-hykin/quik_config_python for a complete explanation")
                        else:
                            print("\navailable profiles:")
                            for each in available_profiles:
                                print(f"    - {each}")
                            print("\nexample usage:")
                            if all(each.isidentifier() for each in available_profile_names):
                                print(command_prefix+f" @{available_profile_names[0]}")
                                if len(available_profile_names) > 1:
                                    print(command_prefix+f" @{available_profile_names[0]} @{available_profile_names[1]}")
                            else:
                                for each in available_profile_names:
                                    print(command_prefix + f"--profiles='{json.dumps([each])}'")
                    else:
                        print("")
                        print(f"here are the values for: {args_after_help}")
                        for each_profile_name in args_after_help:
                            print("")
                            print(f"    {each_profile_name}:")
                            if each_profile_name in available_profiles:
                                print("        "+yaml_string_value(available_profiles[each_profile_name]).replace("\n","\n        "))
                            else:
                                print("        ! PROFILE NOT FOUND !")
                else:
                    for each_key_string in args_after_help:
                        keys = each_key_string.split(":")
                        found_keys = []
                        item = config
                        failed = False
                        for key in keys:
                            if key in item:
                                found_keys.append(key)
                                item = item[key]
                            else:
                                failed = True
                                found_keys = ":".join(found_keys)
                                found_keys = yaml_string_value(found_keys)
                                item_string = yaml_string_value(item).replace("\n", "\n        ")
                                print(f"    I found: {found_keys}\n    but I couldn't find: '{each_key_string}'\n\n    Value of {found_keys} was:\n        {item_string}")
                        if not failed:
                            found_keys = ":".join(found_keys)
                            item_string = ez_yaml.to_string(obj=item).replace("\n", "\n    ")
                            print(f"   {found_keys} has a default value of:\n    {item_string}")
                # TODO: allow user help to specify help for specific keys
            else:
                if isinstance(help_structure, str):
                    print(help_structure)
                else:
                    print(quik_config_help)
            exit()
        # 
        # find the --profiles
        # 
        new_remaining_args = []
        new_selected_profiles = []
        had_profile_arg = False
        prefix1 = "--profiles="
        prefix2 = "@"
        for each_arg in remaining_args:
            starts_with_prefix1 = each_arg.startswith(prefix1)
            starts_with_prefix2 = each_arg.startswith(prefix2)
            if each_arg.startswith(prefix1):
                prefix = prefix1
                had_profile_arg = True
                assignment = each_arg[len(prefix):]
                try:
                    obj = ez_yaml.to_object(string=assignment)
                    if not isinstance(obj, list):
                        raise Exception(f'''    Value was not a list''')
                    new_selected_profiles += ez_yaml.to_object(string=assignment)
                except Exception as error:
                    raise Exception(f"""
                    
                        ---------------------------------------------------------------------------------
                        When calling: find_and_load("{path}", defaults_for_local_data= *a list* )
                        
                        I was given some arguments: {remaining_args}
                        When looking at this argument: {each_arg}
                        (which was converted to: '''{assignment}''' )
                        
                        I tried to parse that as a yaml, and I expected it to be a list like:
                        When parsing it though I got this error
                        
                        __error__
                        {error}
                        __error__
                        
                        
                        LIKELY SOLUTION:
                            Change the argument to be a valid yaml list
                            ex:
                                '{prefix}[howdy,howdy,howdy]'
                            or
                                {prefix}"[ 'howdy,howdy', 'howdy' ]"
                            or
                                {prefix}'[]'
                        ---------------------------------------------------------------------------------
                    """.replace("\n                    ", "\n"))
            elif each_arg.startswith(prefix2):
                prefix = prefix2
                had_profile_arg = True
                assignment = each_arg[len(prefix):]
                new_selected_profiles += [assignment]
            else:
                new_remaining_args.append(each_arg)
        remaining_args = new_remaining_args
        if had_profile_arg:
            selected_profiles = new_selected_profiles
        
        # 
        # merge in all the profiles
        # 
        for each_option in selected_profiles:
            try:
                config = recursive_update(config, available_profiles[each_option])
            except KeyError as error:
                raise Exception(f"""
                
                    ---------------------------------------------------------------------------------
                    Your local config choices in this file: {local_data_path}
                    selected these options: {selected_profiles}
                    (and there's a problem with this one: {each_option})
                    
                    Your info file: {path}
                    only lists these options available: {list(available_profiles.keys())}
                    Look for "(project)" -> "(profiles)" -> *option*,to see them
                    
                    LIKELY SOLUTION:
                        Edit your local config: {local_data_path}
                        And remove "- {each_option}"
                    ---------------------------------------------------------------------------------
                    
                """.replace("\n                ", "\n"))
        
        # 
        # gather all the direct override args
        # 
        # allow for a little yaml shorthand
        # thing:thing2:value >>> thing: { thing2: value }
        config_args = []
        yaml_shorthand_regex = r"((?:[a-zA-Z0-9_][a-zA-Z0-9_-]*:)+)([\w\W]*)"
        for each in remaining_args:
            match = re.match(yaml_shorthand_regex, each)
            # if shorthand
            if match:
                shorthand_part = match[1]
                value_part = match[2]
                shorthand_parts = shorthand_part.split(":")
                shorthand_parts.pop() # remove the trailing empty string
                new_begining = ": {".join(shorthand_parts) + ": "
                new_end = "\n"+( "}" * (len(shorthand_parts)-1) )
                config_args.append(new_begining + value_part + new_end)
            else:
                config_args.append(each)
        
        config_data_from_cli = []
        for each_original, each_converted in zip(remaining_args, config_args):
            try:
                value = ez_yaml.to_object(string=each_converted)
                if not isinstance(value, dict):
                    raise Exception(f'''the value was not a dictionary''')
                config_data_from_cli.append(value)
            except Exception as error:
                raise Exception(f"""
                
                    ---------------------------------------------------------------------------------
                    When calling: find_and_load("{path}", defaults_for_local_data= *a list* )
                    
                    I was given these arguments: {remaining_args}
                    When looking at this argument: {each_original}
                    (which was converted to: '''{each_converted}''' )
                    
                    I tried to parse it as a yaml string, but received an error:
                    
                    __error__
                    {error}
                    __error__
                    
                    
                    LIKELY SOLUTION:
                        Change the argument to be a valid yaml map
                        ex: 'thing: value'
                    ---------------------------------------------------------------------------------
                """.replace("\n                    ", "\n"))
        # 
        # merge in all the cli data
        # 
        for each_dict in config_data_from_cli:
            config = recursive_update(config, each_dict)
    
    # convert everything recursively
    recursive_lazy_dict = lambda arg: arg if not isinstance(arg, dict) else LazyDict({ key: recursive_lazy_dict(value) for key, value in arg.items() })
    dict_output = recursive_lazy_dict(dict(
        config=config,
        path_to=path_to,
        absolute_path_to=absolute_path_to,
        unused_args=unused_args,
        secrets=local_secrets,
        available_profiles=available_profiles,
        selected_profiles=selected_profiles,
        root_path=root_path,
        project=project,
        local_data=local_data,
        as_dict=info,
    ))
    # convert to named tuple for easier argument unpacking
    Info = namedtuple('Info', " ".join(list(dict_output.keys())))
    return Info(**dict_output)

def yaml_string_value(value):
    # remove the "--%YAML 1.2" stuff and trailing newline
    return ez_yaml.to_string(obj=value)[14:-1]

def recursive_copy(a_value):
    if isinstance(a_value, dict):
        new = {}
        for each_key, each_value in a_value.items():
            new[each_key] = recursive_copy(each_value)
        return new
    elif isinstance(a_value, (list, tuple)):
        return [ recursive_copy(each) for each in a_value ]
    else:
        return a_value

def recursive_update(old_values, new_values):
    if not isinstance(old_values, dict) or not isinstance(new_values, dict):
        raise TypeError('Params of recursive_update should be dicts')

    for key in new_values:
        if isinstance(new_values[key], dict) and isinstance(old_values.get(key), dict):
            old_values[key] = recursive_update(old_values[key], new_values[key])
        else:
            old_values[key] = new_values[key]

    return old_values

def resolve_profiles(available_profiles, path):
    import math
    resolved_profiles = {}
    pending_inheriting_profiles = dict(available_profiles)
    prev_number_of_pending_inherits = math.inf
    while len(pending_inheriting_profiles) > 0:
        # make a copy because we're going to be editing the pending_inheriting_profiles, which would screw with the iteration
        copy = dict(pending_inheriting_profiles)
        
        # check for no-progress (which means circular dependency)
        number_of_pending_inherits = sum(len(each.get("(inherit)", [])) for each in copy.values()) + len(copy)
        if number_of_pending_inherits != prev_number_of_pending_inherits:
            # keep track of previous
            prev_number_of_pending_inherits = number_of_pending_inherits
        else:
            print(f"\n\nWarning: there appears to be circular inheritance somewhere among these profiles\nNote this is coming from: {path}\n")
            inherits = tuple((each_key, each["(inherit)"]) for each_key, each in copy.items() if "(inherit)" in each)
            for each_key, each_list in inherits:
                print(f'''    {each_key}: {each_list}''')
            print()
            break
        
        # actually resolve the profiles
        for each_profile_name, each_profile in copy.items():
            if "(inherit)" not in each_profile:
                resolved_profiles[each_profile_name] = pending_inheriting_profiles[each_profile_name]
                del pending_inheriting_profiles[each_profile_name]
            else:
                new_parents = []
                if not isinstance(each_profile["(inherit)"], (list, tuple)):
                    raise Exception(f'''\n\nin the '{path}' file,\nthe {each_profile_name} profile has an (inherit): key\nBut its not a list, and it needs to be a list of strings''')
                for each_parent in reversed(each_profile["(inherit)"]):
                    if each_parent not in available_profiles:
                        if not isinstance(each_profile["(inherit)"], (list, tuple)):
                            raise Exception(f'''\n\nin the '{path}' file,\nthe {each_profile_name} profile has an (inherit): key\nAnd one of the things its trying to inherit from is: {each_parent}\nThe problem is I don't see a {each_parent} profile.\n\nAvailable Profiles: {list(available_profiles.keys())}''')
                    # parent is resolved
                    if each_parent in resolved_profiles:
                        parent_profile = resolved_profiles[each_parent]
                        # 
                        # perform the inheritance
                        # 
                        pending_inheriting_profiles[each_profile_name] = recursive_update(recursive_copy(parent_profile), pending_inheriting_profiles[each_profile_name])
                        continue
                    # parent is not resolved (skip for now)
                    else:
                        new_parents.append(each_parent)
                pending_inheriting_profiles[each_profile_name]["(inherit)"] = new_parents
                # remove key once all resolved
                if len(new_parents) == 0:
                    del pending_inheriting_profiles[each_profile_name]["(inherit)"]
                
    return resolved_profiles

import sys
import os
from os.path import isabs, isfile, isdir, join, dirname, basename, exists, splitext, relpath
from os import remove, getcwd, makedirs, listdir, rename, rmdir, system
from shutil import move
from pathlib import Path
import glob
import shutil

# 
# create a class for generate filesystemtem management
# 
class FileSystem():
    @classmethod
    def write(self, data, to=None):
        # make sure the path exists
        FileSystem.create_folder(os.path.dirname(to))
        with open(to, 'w') as the_file:
            the_file.write(str(data))
    
    @classmethod
    def read(self, filepath):
        try:
            with open(filepath,'r') as f:
                output = f.read()
        except:
            output = None
        return output    
        
    @classmethod
    def delete(self, filepath):
        if isdir(filepath):
            shutil.rmtree(filepath)
        else:
            try:
                os.remove(filepath)
            except:
                pass
    
    @classmethod
    def create_folder(self, path):
        try:
            os.makedirs(path)
        except:
            pass
        
    @classmethod
    def copy(self, from_=None, to=None, new_name="", force= True):
        if new_name == "":
            raise Exception('FileSystem.copy() needs a new_name= argument:\n    FileSystem.copy(from_="location", to="directory", new_name="")\nif you want the name to be the same as before do new_name=None')
        elif new_name is None:
            new_name = os.path.basename(from_)
        
        # get the full path
        to = os.path.join(to, new_name)
        # if theres a file in the target, delete it
        if force and FileSystem.exists(to):
            FileSystem.delete(to)
        # make sure the containing folder exists
        FileSystem.create_folder(os.path.dirname(to))
        if os.path.isdir(from_):
            shutil.copytree(from_, to)
        else:
            return shutil.copy(from_, to)
    
    @classmethod
    def move(self, from_=None, to=None, new_name="", force= True):
        if new_name == "":
            raise Exception('FileSystem.move() needs a new_name= argument:\n    FileSystem.move(from_="location", to="directory", new_name="")\nif you want the name to be the same as before do new_name=None')
        elif new_name is None:
            new_name = os.path.basename(from_)
        
        # get the full path
        to = os.path.join(to, new_name)
        # make sure the containing folder exists
        FileSystem.create_folder(os.path.dirname(to))
        shutil.move(from_, to)
    
    @classmethod
    def exists(self, *args):
        return FileSystem.does_exist(*args)
    
    @classmethod
    def does_exist(self, path):
        return os.path.exists(path)
    
    @classmethod
    def is_folder(self, *args):
        return FileSystem.is_directory(*args)
        
    @classmethod
    def is_dir(self, *args):
        return FileSystem.is_directory(*args)
        
    @classmethod
    def is_directory(self, path):
        return os.path.isdir(path)
    
    @classmethod
    def is_file(self, path):
        return os.path.isfile(path)

    @classmethod
    def list_files(self, path="."):
        return [ x for x in FileSystem.ls(path) if FileSystem.is_file(x) ]
    
    @classmethod
    def list_folders(self, path="."):
        return [ x for x in FileSystem.ls(path) if FileSystem.is_folder(x) ]
    
    @classmethod
    def ls(self, filepath="."):
        glob_val = filepath
        if os.path.isdir(filepath):
            glob_val = os.path.join(filepath, "*")
        return glob.glob(glob_val)

    @classmethod
    def touch(self, path):
        FileSystem.create_folder(FileSystem.dirname(path))
        if not FileSystem.exists(path):
            FileSystem.write("", to=path)
    
    @classmethod
    def touch_dir(self, path):
        FileSystem.create_folder(path)
    
    @classmethod
    def dirname(self, path):
        return os.path.dirname(path)
    
    @classmethod
    def basename(self, path):
        return os.path.basename(path)
    
    @classmethod
    def extname(self, path):
        filename, file_extension = os.path.splitext(path)
        return file_extension
    
    @classmethod
    def path_pieces(self, path):
        """
        example:
            *folders, file_name, file_extension = FileSystem.path_pieces("/this/is/a/filepath.txt")
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
    
    @classmethod
    def join(self, *paths):
        return os.path.join(*paths)
    
    @classmethod
    def absolute_path(self, path):
        return os.path.abspath(path)
    
    @classmethod
    def make_absolute_path(self, path):
        return os.path.abspath(path)
    
    @classmethod
    def make_relative_path(self, *, to, coming_from):
        return os.path.relpath(to, coming_from)

    @classmethod
    def pwd(self):
        return os.getcwd()

FS = FileSystem