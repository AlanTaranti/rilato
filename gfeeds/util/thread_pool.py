import threading
from typing import Any, Callable, Iterable, List
from gi.repository import GLib


class ThreadPool:
    def __init__(
            self,
            max_threads: int,
            worker_func: Callable,
            worker_func_args_l: Iterable[Iterable[Any]],
            final_callback: Callable,
            final_callback_args: Iterable[Any]
    ):
        self.worker_func = worker_func
        self.worker_func_args_l = worker_func_args_l
        self.max_threads = max_threads
        self.final_callback = final_callback
        self.final_callback_args = final_callback_args
        self.waiting_threads: List[threading.Thread] = []
        self.running_threads: List[threading.Thread] = []
        for args_tuple in self.worker_func_args_l:
            self.waiting_threads.append(
                threading.Thread(
                    group=None,
                    target=self._pool_worker,
                    name=None,
                    args=(*args_tuple,),
                    daemon=True
                )
            )

    def _pool_worker(self, *args):
        self.worker_func(*args)
        GLib.idle_add(self._rearrange_pool, threading.current_thread())

    def _rearrange_pool(self, t):
        self.running_threads.remove(t)
        self.start()

    def start(self):
        while (
                len(self.running_threads) < self.max_threads and
                len(self.waiting_threads) > 0
        ):
            t = self.waiting_threads.pop(0)
            t.start()
            self.running_threads.append(t)
        if len(self.running_threads) == 0 and len(self.waiting_threads) == 0:
            self.final_callback(*self.final_callback_args)
