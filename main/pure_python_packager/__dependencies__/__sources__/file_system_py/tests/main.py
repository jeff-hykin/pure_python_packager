#!/usr/bin/env python
import file_system_py as FS

print("testing")

*folders, name, extension = FS.path_pieces("/this/is/a/filepath.txt")
print(f'''*folders = {folders}''')
print(f'''name = {name}''')
print(f'''extension = {extension}''')

FS.remove("./logs/a folder")
FS.remove("./logs/a file")

FS.ensure_is_file("./logs/thing/thing.txt")
FS.clear_a_path_for("./logs/thing/thing.txt", overwrite=True)

print("FS.basename", FS.basename("./logs/thing/things.log.ttxt"))
print("FS.name", FS.name("./logs/thing/things.log.ttxt"))
print("FS.extname", FS.extname("./logs/thing/things.log.ttxt"))
print("FS.without_ext", FS.without_ext("./logs/thing/things.log.ttxt"))
print("FS.without_any_ext", FS.without_any_ext("./logs/thing/things.log.ttxt"))
print("FS.list_paths_in", FS.list_paths_in("./logs/thing/things"))
print("FS.list_basenames_in", FS.list_basenames_in("./logs/thing/things"))
print("FS.list_file_paths_in", FS.list_file_paths_in("./logs/thing/things"))
print("FS.list_folder_paths_in", FS.list_folder_paths_in("./logs/thing/things"))