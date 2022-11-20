import json
from typing import Callable, Dict, Union
from gi.repository import GLib, Gio
from datetime import datetime


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return super().default(o)


class CustomJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, object_hook=self.obj_hook, **kwargs)

    def obj_hook(self, jdict):
        for (key, value) in jdict.items():
            if isinstance(value, str) and '-' in value and ':' in value:
                try:
                    jdict[key] = datetime.fromisoformat(value)
                except Exception:
                    pass
        return jdict


def __convert_string_variant(v: GLib.Variant) -> Union[str, dict, list]:
    res = v.get_string()
    if (
            (res.startswith('{') and res.endswith('}')) or
            (res.startswith('[') and res.endswith(']'))
    ):
        return json.loads(res, cls=CustomJSONDecoder)
    return res


GSETTINGS_TYPES = Union[str, int, float, bool, dict, list]
VARIANT_CONVERTERS: Dict[str, Callable[[GLib.Variant], GSETTINGS_TYPES]] = {
    's': __convert_string_variant,
    'i': lambda v: int(v.get_int32()),
    'd': lambda v: float(v.get_double()),
    'b': lambda v: v.get_boolean(),
}


class GsettingsWrapper:
    def __init__(self, package: str):
        self.package = package
        if self.package not in Gio.Settings.list_schemas():
            raise KeyError(
                f'GsettingsWrapper: Schema {self.package} not installed'
            )
        self.gs: Gio.Settings = Gio.Settings.new(self.package)
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
        converter = VARIANT_CONVERTERS.get(v.get_type_string(), None)
        if converter is None:
            return self.__type_err()
        return converter(v)

    def set(self, key: str, value: GSETTINGS_TYPES):
        key = self.convert_and_check_key(key)
        match value:
            case str(value):
                self.gs.set_string(key, value)
            case dict(value) | list(value):
                self.set(key, json.dumps(value, cls=CustomJSONEncoder))
            case bool(value):
                self.gs.set_boolean(key, value)
            case int(value):
                self.gs.set_int(key, value)
            case float(value):
                self.gs.set_double(key, value)
            case _:
                return self.__type_err()

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
        }, indent=4, cls=CustomJSONEncoder)
