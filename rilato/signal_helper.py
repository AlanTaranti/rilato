from typing import Literal, Tuple, Type
from gi.repository import GObject

SignalReturnType = (
    Literal[
        GObject.TYPE_INT,
        GObject.TYPE_BOOLEAN,
        GObject.TYPE_VARIANT,
        GObject.TYPE_FLOAT,
        GObject.TYPE_DOUBLE,
        GObject.TYPE_STRING,
        GObject.TYPE_NONE,
        GObject.TYPE_PYOBJECT,
    ]
    | None
)


def signal_tuple(
    flag: GObject.SignalFlags = GObject.SignalFlags.RUN_LAST,
    ret: SignalReturnType = None,
    params: Tuple[Type] = tuple(),
) -> Tuple[GObject.SignalFlags, SignalReturnType, Tuple[Type]]:
    return (flag, ret, params)
