from configuration.config import *

print(config.mtu)
config.mtu = 0
print(config.mtu)
config.save_to_file("configuration/example_config_out.ini")
config.load_from_file("configuration/example_config.ini")
print(config.mtu)
