from configuration.config import *

# print(config.mtu) # Illegal: use before set
config.load_from_file("configuration/example_config.ini")
config.mtu = 1500
config.fragment_timeout = 3
print(config.mtu, config.fragment_timeout)
config.save_to_file("configuration/example_config_out.ini")
