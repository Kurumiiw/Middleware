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
    Annotations (such as _network_properties: ConfigSection and mtu: int) are
    used to generate getters and settes automatically. This is ONLY done for
    annotations, not variables. ALL config variables must therefore have no
    default value (this is by design).

    The INI file format is used for serializing the configuration and the
    format of the annotations below are made to reflect this. Annotations with
    the type 'ConfigSection' are regarded as section names (specified as [name]
    in the INI file). Every annotation below a section, before the next section
    annotation, is regarded as part of this section (e.g. mtu is regarded as
    part of the network_properties section). Annotations belonging to a section
    are added to the generated class with generated getters, setters and
    serialization/deserialization. Sections are not added to the generated
    class, and trying to access e.g. config.network_properties will fail.
    Additionally, all variables belonging to a section must be set in the
    config file for it to be valid.

    Config variables are generated as properties, meaning they behave as
    normal variables, except that when accessing normally the getter is called,
    and the setter when set (i.e config.mtu calls the getter for mtu). Each
    config variables has it's own getter and setter which calls the common
    get_var and set_var. This is to allow overriding what happens when a
    variables is get/set (e.g. when a system config var is set, set_var might
    do a system call to also set this in the kernel). When no special action
    is wanted the 'default_generated_*et_var' is supplied, which just sets/gets
    the variables normally.
    """
    network_properties: ConfigSection
    mtu: int

    middleware_configuration: ConfigSection
    fragment_timeout: int
    expected_congestion: int
    expected_bandwidth: int
    expected_packet_loss: int
    expected_jitter: int

    system_configuration: ConfigSection
    # see https://docs.kernel.org/networking/ip-sysctl.html
    # NOTE: all boolean values are marked as int due to the c type system treating them this way
    tcp_frto: int
    tcp_reflect_tos: int
    tcp_sack: int

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
        #assert self.default_generated_get_var(var_name) != None, "Config variables must be set before usage"
        return self.default_generated_get_var(var_name)

    def set_var(self, var_name: str, value: any):
        if var_name in self._system_configuration_var_list:
            if var_name == "tcp_frto":
                os.system("sysctl -w net.ipv4.tcp_frto={}".format(value))
            elif var_name == "tcp_reflect_tos":
                os.system("sysctl -w net.ipv4.tcp_reflect_tos={}".format(value))
            elif var_name == "tcp_sack":
                os.system("sysctl -w net.ipv4.tcp_sack={}".format(value))

        return self.default_generated_set_var(var_name, value)

    def load_from_file(self, path: str):
        section_names = self._section_names
        var_lists = self._var_lists

        conf_reader = configparser.ConfigParser()
        conf_reader.read(path)

        if conf_reader.sections() != section_names:
            if not(set(conf_reader.sections()).issubset(section_names)):
                raise ConfigParsingError("Invalid sections: {}".format(set(conf_reader.sections()) - set(section_names)))
            else:
                raise ConfigParsingError("Missing sections: {}".format(set(section_names) - set(conf_reader.sections())))
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
