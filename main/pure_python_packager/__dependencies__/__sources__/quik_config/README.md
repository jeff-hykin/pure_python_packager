# What is this?

A config system that doesn't waste your time
- per-machine settings that stay in sync
- a consistent way to handle filepaths (stop hardcoding filepaths as python strings!)
- hierarchical, with inheritable groups of settings (profiles)
- default works along side `argparse`, but also can just replace it entirely for rapid development
- all values in the hierarchy can be overridden with CLI args
- select multiple profiles from CLI (ex: GPU & DEV or UNIX & GPU & PROD)
- can combine/import multiple config files

# How do I use this?

`pip install quik-config`

In a `config.py`: 
```python
from quik_config import find_and_load

info = find_and_load(
    "info.yaml", # walks up folders until it finds a file with this name
    cd_to_filepath=True, # helpful if using relative paths
    fully_parse_args=True, # if you already have argparse, use parse_args=True instead
    show_help_for_no_args=False, # change if you want
)

print(info.config) # dictionary
```

Create `info.yaml` with a structure like this:
```yaml
# names in parentheses are special, all other names are not!
# (e.g. add/extend this with any custom fields)
(project):
    # the local_data file will be auto-generated
    # (its for machine-specific data)
    # so probably git-ignore whatever path you pick
    (local_data): ./local_data.ignore.yaml
    
    # example profiles
    (profiles):
        (default):
            blah: "blah blah blah"
            mode: development # or production. Same thing really
            has_gpu: maybe
            constants:
                pi: 3 # its 'bout 3 
        
        PROFILE1:
            constants:
                e: 2.7182818285
        
        PROD:
            mode: production
            constants:
                pi: 3.1415926536
                problems: true
```

Then run it:
```shell
python ./config.py
```

Which will print out this config:
```py
{
    "blah": "blah blah blah", # from (default)
    "mode": "development",    # from (default)
    "has_gpu": "maybe",       # from (default)
    "constants": {
        "pi": 3,              # from (default)
    },
}
```

# Features

### Builtin Help

```shell
python ./config.py --help --profiles
```

```
available profiles:
    - DEV
    - GPU
    - PROD

as cli argument:
   -- --profiles='["DEV"]'
   -- --profiles='["GPU"]'
   -- --profiles='["PROD"]'
```


```
    ---------------------------------------------------------------------------------
    QUIK CONFIG HELP
    ---------------------------------------------------------------------------------
    
    open the file below and look for "(profiles)" for more information:
        $PWD/info.yaml
    
    examples:
        python3 ./ur_file.py   --  --help --profiles
        python3 ./ur_file.py   --  --help key1
        python3 ./ur_file.py   --  --help key1:subKey
        python3 ./ur_file.py   --  --help key1:subKey key2
        python3 ./ur_file.py   --  --profiles='[YOUR_PROFILE, YOUR_OTHER_PROFILE]'
        python3 ./ur_file.py   --  thing1:"Im a new value"          part2:"10000"
        python3 ./ur_file.py   --  thing1:"I : cause errors"        part2:10000
        python3 ./ur_file.py   --  'thing1:"I : dont cause errors"  part2:10000
        python3 ./ur_file.py   --  'thing1:["Im in a list"]'
        python3 ./ur_file.py   --  'thing1:part_A:"Im nested"'
        python3 ./ur_file.py "I get sent to ./ur_file.py" --  part2:"new value"
        python3 ./ur_file.py "I get ignored" "me too"  --  part2:10000
    
    how it works:
        - the "--" is a required argument, quik config only looks after the --
        - given "thing1:10", "thing1" is the key, "10" is the value
        - All values are parsed as json/yaml
            - "true" is boolean true
            - "10" is a number
            - '"10"' is a string (JSON escaping)
            - '"10\n"' is a string with a newline
            - '[10,11,hello]' is a list with two numbers and an unquoted string
            - '{"thing": 10}' is a map/object
            - "blah blah" is an un-quoted string with a space. Yes its valid YAML
            - multiline values are valid, you can dump an whole JSON doc as 1 arg
        - "thing1:10" overrides the "thing1" in the (profiles) of the info.yaml
        - "thing:subThing:10" is shorthand, 10 is the value, the others are keys
          it will only override the subThing (and will create it if necessary)
        - '{"thing": {"subThing":10} }' is long-hand for "thing:subThing:10"
        - '"thing:subThing":10' will currently not work for shorthand (parse error)
    
    options:
        --help
        --profiles
    
    ---------------------------------------------------------------------------------
    
    your default top-level keys:
        - mode
        - has_gpu
        - constants
    your local defaults file:
        ./local_data.ignore.yaml
    your default profiles:
        - DEV
    
    ---------------------------------------------------------------------------------

```


### Select Profiles from CLI

```shell
python ./config.py @PROFILE1
```

prints:
```py
{
    "blah": "blah blah blah", # from (default)
    "mode": "development",    # from (default)
    "has_gpu": "maybe",       # from (default)
    "constants": {
        "pi": 3.1415926536,   # from (default)
        "e": 2.7182818285,    # from PROFILE1
    },
}
```

```shell
python ./config.py @PROFILE1 @PROD
```

prints:
```py
{
    "blah": "blah blah blah", # from (default)
    "mode": "production",     # from PROD
    "has_gpu": "maybe",       # from (default)
    "constants": {
        "pi": 3.1415926536,   # from (default)
        "e": 2.7182818285,    # from PROFILE1
        "problems": True,     # from PROD
    },
}
```

### Override Values from CLI

```shell
python ./config.py @PROFILE1 mode:custom constants:problems:99
```

prints:
```py
{
    "blah": "blah blah blah", # from (default)
    "mode": "custom",         # from CLI
    "has_gpu": "maybe",       # from (default)
    "constants": {
        "pi": 3.1415926536,   # from (default)
        "e": 2.7182818285,    # from PROFILE1
        "problems": 99,       # from CLI
    },
}
```

Again but with really complicated arguments: <br>
(each argument is parsed as yaml)

```shell
python ./run.py arg1 --  mode:my_custom_mode  'constants: { tau: 6.2831853072, pi: 3.1415926, reserved_letters: [ "C", "K", "i" ] }'
```

prints:
```py
config: {
    "mode": "my_custom_mode", 
    "has_gpu": False, 
    "constants": {
        "pi": 3.1415926, 
        "tau": 6.2831853072, 
        "reserved_letters": ["C", "K", "i", ], 
    }, 
}
unused_args: ["arg1"]
```

### Working Alongside Argparse (quick)

Remove `fully_parse_args` and replace it with just `parse_args`

```py
info = find_and_load(
    "info.yaml",
    parse_args=True, # <- will only parse after -- 
)
```

Everthing in the CLI is the same, but it waits for `--`
For example:

```shell
# quik_config ignores arg1 --arg2 arg3, so argparse can do its thing with them
python ./config.py arg1 --arg2 arg3 -- @PROD
```

### Working Alongside Argparse (advanced)

Arguments can simply be passed as a list of strings, which can be useful for running many combinations of configs.

```py
info = find_and_load(
    "info.yaml",
    args=[ "@PROD" ],
)
```

### Relative and absolute paths

Add them to the info.yaml

```yaml
(project):
    (local_data): ./local_data.ignore.yaml
    
    # filepaths (relative to location of info.yaml)
    (path_to):
        this_file:       "./info.yaml"
        blah_file:       "./data/results.txt"
    
    # example profiles
    (profiles):
        (default):
            blah: "blah blah blah"
```

Access them in python
```py
info = find_and_load("info.yaml")
info.path_to.blah_file
info.absolute_path_to.blah_file # nice when then PWD != folder of the info file
```

### Import other yaml files
FIXME

## Different Profiles For Different Machines

Lets say you've several machines and an info.yaml like this:
```yaml
(project):
    (profiles):
        DEV:
            cores: 1
            database_ip: 192.168.10.10
            mode: dev
        LAPTOP:
            cores: 2
        DESKTOP:
            cores: 8
        UNIX:
            line_endings: "\n"
        WINDOWS:
            line_endings: "\r\n"
        PROD:
            database_ip: 183.177.10.83
            mode: prod
            cores: 32
```

And lets say you have a `config.py` like this:
```python
from quik_config import find_and_load
info = find_and_load(
    "info.yaml",
    defaults_for_local_data=["DEV", ],
    # if the ./local_data.ignore.yaml doesnt exist,
    # => create it and add DEV as the default no-argument choice
)
```

Run the code once to get a `./local_data.ignore.yaml` file. <br>

Each machine gets to pick the profiles it defaults to.<br>
So, on your Macbook you can edit the `./local_data.ignore.yaml` to include something like the following:
```yaml
(selected_profiles):
    - LAPTOP # the cores:2 will be used (instead of cores:1 from DEV)
    - UNIX   #     because LAPTOP is higher in the list than DEV
    - DEV
```

On your Windows laptop you can edit it and put:
```yaml
(selected_profiles):
    - LAPTOP
    - WINDOWS
    - DEV
```

## Command Line Arguments

If you have `run.py` like this:

```python
from quik_config import find_and_load

info = find_and_load("info.yaml", parse_args=True)

print("config:",      info.config     )
print("unused_args:", info.unused_args)

# 
# call some other function you've got
# 
#from your_code import run
#run(*info.unused_args)
```

### Example 0

Using the python file and config file above

```shell
python ./run.py
```

Running that will output:

```py
config: {
    "mode": "development",
    "has_gpu": False,
    "constants": {
        "pi": 3
    }
}
unused_args: []
```

### Example 1

Show help. This output can be overridden in the info.yaml by setting `(help):` under the `(project):` key.

```shell
python ./run.py -- --help
```

Note the `--` is needed in front of the help.

You can also add `show_help_for_no_args=True` if you want that behavior. <br>
Ex:

```python
from quik_config import find_and_load
info = find_and_load(
    "info.yaml",
    show_help_for_no_args=True
    parse_args=True,
)
```

### Example 2

Again but selecting some profiles

```shell
python ./run.py arg1 -- --profiles='[PROD]'
# or
python ./run.py arg1 -- @PROD
```

Output:

```py
config: {
    "mode": "production",
    "has_gpu": False,
    "constants": {
        "pi": 3.1415926536,
        "problems": True,
    },
}
unused_args: ["arg1"]
```

### Example 3

Again but with custom arguments:

```shell
python ./run.py arg1 --  mode:my_custom_mode  constants:tau:6.2831853072
```

```py
config: {
    "mode": "my_custom_mode",
    "has_gpu": False,
    "constants": {
        "pi": 3,
        "tau": 6.2831853072,
    },
}
unused_args: ["arg1"]
```

### Example 4

Again but with really complicated arguments: <br>
(each argument is parsed as yaml)

```shell
python ./run.py arg1 --  mode:my_custom_mode  'constants: { tau: 6.2831853072, pi: 3.1415926, reserved_letters: [ "C", "K", "i" ] }'
```

prints:

```py
config: {
    "mode": "my_custom_mode", 
    "has_gpu": False, 
    "constants": {
        "pi": 3.1415926, 
        "tau": 6.2831853072, 
        "reserved_letters": ["C", "K", "i", ], 
    }, 
}
unused_args: ["arg1"]
```


<!-- 
TODO:
- make argument parsing not need the -- by default
- allow for multiple back to back runs with different args
 -->