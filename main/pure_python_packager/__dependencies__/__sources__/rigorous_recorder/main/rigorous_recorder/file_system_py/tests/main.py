#!/usr/bin/env python
import file_system_py as FS


*folders, name, extension = FS.path_pieces("/this/is/a/filepath.txt")
print(f'''*folders = {folders}''')

FS.remove("./logs/a folder")
FS.remove("./logs/a file")

FS.ensure_is_file("./logs/thing/thing.txt")
FS.clear_a_path_for("./logs/thing/thing.txt", overwrite=True)

print(FS.list_paths_in("./logs/thing/things"))
print(FS.list_basenames_in("./logs/thing/things"))
print(FS.list_file_paths_in("./logs/thing/things"))
print(FS.list_folder_paths_in("./logs/thing/things"))