from dataclasses import dataclass
import configparser

@dataclass
class Config:
    # GivenProperties
    mtu: int = 500 # Maximum Transmission Unit measured in bytes

    # ExpectedProperties

    # Tuning
    

class InvalidConfigFormat(ValueError):
    """
    Raised when parsing an ill-formatted config file
    """
    pass

def load_config_from_file(file_path: str) -> Config:
    """
    Loads and parses a config file, resulting values are stored in the returned Config object.
    """
    result_config = Config()

    conf_reader = configparser.ConfigParser()
    conf_reader.read(file_path)

    sections = set(conf_reader.sections())
    correct_sections = {"GivenProperties", "ExpectedProperties", "Tuning"}
    if sections != correct_sections:
        if sections.issubset(correct_sections):
            raise InvalidConfigFormat("Invalid config file. Missing sections: {}.".format(", ".join(correct_sections - sections)))
        elif len(sections - correct_sections) > 0:
            raise InvalidConfigFormat("Invalid config file. Illegal sections: {}.".format(", ".join(sections - correct_sections)))
        else:
            raise InvalidConfigFormat("Invalid config file. Invalid sections.")
    else:
        for section in sections:
            for key in conf_reader[section]:
                # TODO: verify 'key' is a field in the correct section
                setattr(result_config, key, conf_reader[section][key])

    return result_config

def save_config_to_file(config: Config, file_path: str):
    """
    Generates an equivalent ini configuration string and saves it to the specified file.
    """
    with open(file_path, "w") as config_file:
        conf_writer = configparser.ConfigParser()

        conf_writer.add_section("GivenProperties")
        # TODO: automate
        conf_writer.set("GivenProperties", "mtu", str(500))

        conf_writer.add_section("ExpectedProperties")

        conf_writer.add_section("Tuning")

        conf_writer.write(config_file, space_around_delimiters = True)

c = load_config_from_file("example_config.ini")
print(c)
save_config_to_file(c, "example_config_out.ini")
