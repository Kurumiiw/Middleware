import collections

config_var_list_entry = collections.namedtuple("config_var_list_entry", "name type")


def generate_config(conf_class: type) -> type:
    class Config:
        pass

    variables = [key for key in conf_class.__annotations__]
    variables = list(filter(lambda name: not name.startswith("__"), variables))

    Config._var_list = [
        config_var_list_entry(var, conf_class.__annotations__[var]) for var in variables
    ]

    for var in variables:
        setattr(Config, "_" + var, None)

        setattr(
            Config,
            var,
            property(
                fget=lambda self, name=var: self.get_var(name),
                fset=lambda self, value, name=var: self.set_var(name, value),
            ),
        )

    def default_get_var(self, var):
        return getattr(self, "_" + var)

    def default_set_var(self, var, value):
        setattr(self, "_" + var, value)

    Config.default_generated_get_var = default_get_var
    Config.default_generated_set_var = default_set_var

    Config.get_var = conf_class.get_var
    Config.set_var = conf_class.set_var

    Config.load_from_file = conf_class.load_from_file
    Config.save_to_file = conf_class.save_to_file

    def __setattr__(self, key, value):
        assert key in vars(Config), "Config has no member {}".format(key)
        object.__setattr__(self, key, value)

    Config.__setattr__ = __setattr__

    return Config
