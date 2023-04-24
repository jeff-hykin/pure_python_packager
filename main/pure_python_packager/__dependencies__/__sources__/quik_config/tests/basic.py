from quik_config import find_and_load

info = find_and_load(
    "info.yaml", # walks up folders until it finds the 
    cd_to_filepath=True,
    parse_args=True,
    defaults_for_local_data=["PROD"], # example profiles
)

print(info.config) # dictionary