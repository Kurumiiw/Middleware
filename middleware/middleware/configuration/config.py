from .generate_config import *
import configparser
import os


class ConfigParsingError(ValueError):
    pass


@generate_config
class Config:
    """
    Class that hold configuration values and a method of getting, setting
    loading and saving these.

    The content of this class is generated based on the template given below.
    Annotations (mtu: int) are used to generate getters and settes automatically.
    This is ONLY done for annotations, not variables. ALL config variables must
    therefore have no default value (this is by design).

    The INI file format is used for serializing the configuration and the
    format of the annotations below are made to reflect this. Annotations
    are added to the generated class with generated getters, setters and
    serialization/deserialization. Additionally, all variables must be set in the
    config file for it to be valid.

    Config variables are generated as properties, meaning they behave as
    normal variables, except that when accessing normally the getter is called,
    and the setter when set (i.e config.mtu calls the getter for mtu). Each
    config variables has it's own getter and setter which calls the common
    get_var and set_var. This is to allow overriding what happens when a
    variables is get/set. When no special action is wanted the
    'default_generated_*et_var' is supplied, which just sets/gets the
    variables normally.
    """

    mtu: int
    fragment_timeout: int
    congestion_algorithm: str
    echo_config_path: bool

    def get_var(self, var_name: str) -> any:
        # NOTE: This is just a check to avoid using config variables
        #       without them being set first. I assume None is not
        #       not a valid config value and therefore use it as a
        #       sentinel tp check this. If this is not wanted, change
        #       this assert, and if setting the config variables to
        #       None initially is not wanted, this must be changed
        #       in generate_config (they have to be set with a value
        #       to be registered as a variable, so None has to be
        #       replaced with some other value, and the set cannot be
        #       omitted)
        assert (
            self.default_generated_get_var(var_name) != None
        ), "Config variables must be set before usage"
        return self.default_generated_get_var(var_name)

    def set_var(self, var_name: str, value: any):
        return self.default_generated_set_var(var_name, value)

    def load_from_file(self, path: str):
        conf_reader = configparser.ConfigParser()
        conf_reader.read(path)

        section_name = "middleware_configuration"
        if conf_reader.sections() != [section_name]:
            raise ConfigParsingError(
                "Invalid sections: {}. Only legal section is {}".format(
                    set(conf_reader.sections()), section_name
                )
            )
        else:
            var_list = Config._var_list
            var_names = [var.name for var in var_list]

            if set(conf_reader.options(section_name)) != set(var_names):
                raise ConfigParsingError(
                    "Missing variables: {}".format(
                        set(var_names) - set(conf_reader.options(section_name))
                    )
                )
            else:
                for var in var_list:
                    value = conf_reader.get(section_name, var.name)

                    if var.type == int:
                        try:
                            value = int(value)
                        except:
                            raise ConfigParsingError(
                                "Cannot set {} to {}. Illegal integral value.".format(
                                    var.name, value
                                )
                            )
                    elif var.type == bool:
                        if value == "True":
                            value = True
                        elif value == "False":
                            value = False
                        else:
                            raise ConfigParsingError(
                                "Cannot set {} to {}. Illegal boolean value.".format(
                                    var.name, value
                                )
                            )
                    elif var.type == str:
                        value = value  # Strings are kept as is, no quotation
                    elif var.type == float:
                        try:
                            value = float(value)
                        except:
                            raise ConfigParsingError(
                                "Cannot set {} to {}. Illegal floating point value.".format(
                                    var.name, value
                                )
                            )
                    else:
                        assert False, "Not implemented"

                    self.set_var(var.name, value)

    def save_to_file(self, path: str):
        conf_writer = configparser.ConfigParser()

        section_name = "middleware_configuration"
        conf_writer.add_section(section_name)

        for var in Config._var_list:
            conf_writer.set(section_name, var.name, str(self.get_var(var.name)))

        with open(path, "w") as file_writer:
            conf_writer.write(file_writer, space_around_delimiters=True)


config = Config()


def _load_config():
    cwd = os.getcwd()
    cwd_config_path = os.path.join(cwd, "middleware_config.ini")

    chosen_path: str
    if os.path.isfile(cwd_config_path):
        chosen_path = cwd_config_path
    else:
        chosen_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "middleware_config.ini"
        )

    config.load_from_file(chosen_path)
    if config.echo_config_path:
        print("Middleware config loaded from {}".format(chosen_path))


_load_config()
