def generate_config(conf_class: type) -> type:
    class Config:
        pass

    variables_to_filter_out = ["get_var", "set_var", "load_from_file", "save_to_file"]
    variables = [key for key in vars(conf_class)]
    variables = list(filter(lambda name: not name.startswith("__"), variables))
    variables = list(filter(lambda name: name not in variables_to_filter_out, variables))

    section_names = ["_network_properties", "_middleware_configuration", "_system_configuration"]
    Config._section_names = section_names
    assert variables[0] == section_names[0], "Missing section marker for NetworkProperties"
    assert section_names[1] in variables, "Missing section marker for MiddlewareConfiguration"
    assert section_names[2] in variables, "Missing section marker for SystemConfiguration"

    assert set(conf_class.__annotations__.keys()).issubset(variables), "All configuration variables need a default value"

    Config._network_properies_var_list = []
    Config._middleware_configuration_var_list = []
    Config._system_configuration_var_list = []

    var_lists = [
        Config._network_properies_var_list,
        Config._middleware_configuration_var_list,
        Config._system_configuration_var_list
    ]
    Config._var_lists = var_lists

    # NOTE: [1:] to skip first section marker
    for var in variables[1:]:
        if var in section_names:
            var_lists = var_lists[1:]
        else:
            var_lists[0].append(var)

    for var in filter(lambda name: name not in section_names, variables):
        setattr(Config, "_"+var, getattr(conf_class, var))

        def get_var(self):
            return self.get_var(var)

        def set_var(self, value):
            self.set_var(var, value)

        setattr(Config, "get_"+var, get_var)
        setattr(Config, "set_"+var, set_var)
        setattr(Config, var, property(fget=getattr(Config, "get_"+var), fset=getattr(Config, "set_"+var)))

    def default_get_var(self, var):
        return getattr(self, "_"+var)

    def default_set_var(self, var, value):
        setattr(self, "_"+var, value)

    Config.default_generated_get_var =  default_get_var
    Config.default_generated_set_var = default_set_var

    Config.get_var = conf_class.get_var
    Config.set_var = conf_class.set_var

    Config.load_from_file = conf_class.load_from_file
    Config.save_to_file = conf_class.save_to_file

    return Config
