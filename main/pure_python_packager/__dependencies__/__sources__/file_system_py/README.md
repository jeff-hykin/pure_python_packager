# What is this?

An work-in-progress library for file manipulation in python. <br>
(E.g. I was tired of copy-pasting my giant tool into each project)

# How do I use this?

`pip install file-system-py`


```python
import file_system_py as FS


*folders, name, extension = FS.path_pieces("/this/is/a/filepath.txt")
# folder[0] == '/' for absolute paths

FS.remove("./a folder")
FS.remove("./a file")
# 1. no error if they dont exist
# 2. doesnt care if file or folder

FS.extname("./thing/thing.stuff.blah.py")
# returns ".py"

# different ways to list
FS.list_paths_in("./thing/things")
FS.list_basenames_in("./thing/things")
FS.list_file_paths_in("./thing/things")
FS.list_folder_paths_in("./thing/things")
# returns [] when path doesnt exist or is a file

# much faster iterative versions
FS.iterate_paths_in(path)
FS.iterate_basenames_in(path)
FS.iterate_file_paths_in(path)
FS.iterate_folder_paths_in(path)


# 
# full api
# 
FS.walk_up_until(file_to_find, start_path=get_cwd())
FS.ensure_is_folder(path, force=True)
FS.ensure_is_file(path, force=True)
FS.make_relative_path(to=, coming_from=get_cwd())
FS.make_absolute_path(to, coming_from=get_cwd())
FS.move(item, to=, new_name=, force=True)
FS.copy(item, to=, new_name=, force=True)
FS.write(data, to=, force=True)
FS.is_folder(path)
FS.is_file(path)
FS.read(filepath)
FS.remove(path)
FS.exists(path)
FS.ls(path=".")
FS.list_paths_in(path)
FS.list_basenames_in(path)
FS.list_file_paths_in(path)
FS.list_folder_paths_in(path)
FS.iterate_paths_in(path)
FS.iterate_basenames_in(path)
FS.iterate_file_paths_in(path)
FS.iterate_folder_paths_in(path)
FS.glob(path)
FS.touch(path)
FS.touch_dir(path)
FS.parent_folder(path)
FS.basename(path)
FS.name(path)
FS.extname(path)
FS.path_pieces(path)
FS.join(*paths)
FS.is_absolute_path(path)
FS.is_relative_path(path)
FS.get_cwd()
FS.local_path(*paths)
```
