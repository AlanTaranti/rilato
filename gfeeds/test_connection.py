import threading
import requests
from gi.repository import Gtk, GLib


def __is_online_async_worker(callback):
    TEST_URL = 'http://httpbin.org/robots.txt'
    EXPECTED_STATUS = 405
    try:
        res = requests.post(TEST_URL)
        print('>>>')
        GLib.idle_add(callback, res.status_code == EXPECTED_STATUS)
    except requests.exceptions.ConnectionError:
        GLib.idle_add(callback, False)


def is_online(callback):
    threading.Thread(
        target=__is_online_async_worker,
        args=(callback,),
        daemon=True
    ).start()
