from quik_config import find_and_load
import sys

print(f'''sys.argv = {sys.argv}''')

info = find_and_load("main/info.yaml", parse_args=True, defaults_for_local_data=["DEV"], cd_to_filepath=True)

print(f'''secrets = {info.secrets}''')
print(f'''unused_args = {info.unused_args}''')
print(f'''config = {info.config}''')
print(f'''path_to = {info.path_to}''')
print(f'''absolute_path_to = {info.absolute_path_to}''')