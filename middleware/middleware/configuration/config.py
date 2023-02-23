from .generate_config import *
import configparser

class ConfigParsingError(ValueError):
    pass

@generate_config
class Config:
    # IMPORTANT: variables have to have a default value
    _network_properties = None
    mtu: int = 500

    _middleware_configuration = None
    _system_configuration = None

    def get_var(self, var_name: str) -> any:
        return self.default_generated_get_var(var_name)

    def set_var(self, var_name: str, value: any):
        return self.default_generated_set_var(var_name, value)

    def load_from_file(self, path: str):
        section_names = self._section_names
        var_lists = self._var_lists

        conf_reader = configparser.ConfigParser()
        conf_reader.read(path)

        if conf_reader.sections() != section_names:
            raise ConfigParsingError("Invalid sections")
        else:
            for section_index, section in enumerate(section_names):
                var_list = var_lists[section_index]
                
                if conf_reader.options(section) != var_list:
                    raise ConfigParsingError("Missing variables")
                else:
                    for var in var_list:
                        self.set_var(var, conf_reader.get(section, var))

    def save_to_file(self, path: str):
        section_names = self._section_names
        var_lists = self._var_lists

        conf_writer = configparser.ConfigParser()

        for section in section_names:
            conf_writer.add_section(section)

        for section_index, section_var_list in enumerate(var_lists):
            section = section_names[section_index]

            for var in section_var_list:
                conf_writer.set(section, var, str(self.get_var(var)))

        with open(path, "w") as file_writer:
            conf_writer.write(file_writer, space_around_delimiters=True)

config = Config()
