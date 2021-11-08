import threading
import requests
from gi.repository import GLib, Gio

__HOSTNAME = 'gnome.org'

def __is_online_async_worker(callback):
    res = False
    try:
        res = Gio.NetworkMonitor.get_default().can_reach(
            Gio.NetworkAddress(hostname=__HOSTNAME)
        )
    except Exception:
        pass
    GLib.idle_add(callback, res)


def is_online(callback):
    threading.Thread(
        target=__is_online_async_worker,
        args=(callback,),
        daemon=True
    ).start()
