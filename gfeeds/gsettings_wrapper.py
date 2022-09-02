import json
from typing import Union
from gi.repository import Gio


GSETTINGS_TYPES = Union[str, int, float, bool, dict, list]


class GsettingsWrapper:
    def __init__(self, package: str):
        self.package = package
        if self.package not in Gio.Settings.list_schemas():
            raise KeyError(
                f'GsettingsWrapper: Schema {self.package} not installed'
            )
        self.gs = Gio.Settings.new(self.package)
        self.__keys = self.gs.keys()

    @property
    def keys(self):
        return self.__keys

    def convert_and_check_key(self, key: str) -> str:
        key = key.replace('_', '-')
        if key not in self.__keys:
            raise KeyError(
                f'GsettingsWrapper: key `{key}` not found in schema'
            )
        return key

    def get(self, key: str) -> GSETTINGS_TYPES:
        key = self.convert_and_check_key(key)
        v = self.gs.get_value(key)
        match v.get_type_string():
            case 's':
                res = v.get_string()
                if (
                        (res.startswith('{') and res.endswith('}')) or
                        (res.startswith('[') and res.endswith(']'))
                ):
                    return json.loads(res)
                return res
            case 'i':
                return int(v.get_int32())
            case 'd':
                return float(v.get_double())
            case 'b':
                return v.get_boolean()
            case _:
                self.__type_err()

    def set(self, key: str, value: GSETTINGS_TYPES):
        key = self.convert_and_check_key(key)
        match value:
            case str(value):
                self.gs.set_string(key, value)
            case dict(value) | list(value):
                self.set(key, json.dumps(value))
            case bool(value):
                self.gs.set_boolean(key, value)
            case int(value):
                self.gs.set_int(key, value)
            case float(value):
                self.gs.set_double(key, value)
            case _:
                self.__type_err()

    def __type_err(self):
        raise TypeError(
            'GsettingsWrapper: Type not supported'
        )

    def __getitem__(self, key: str) -> GSETTINGS_TYPES:
        return self.get(key)

    def __setitem__(self, key: str, value: GSETTINGS_TYPES):
        self.set(key, value)

    def to_json_str(self) -> str:
        return json.dumps({
            k: self.get(k) for k in self.__keys
        }, indent=4)
