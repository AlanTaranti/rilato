# Coding Guidelines

1. **Language & Versions**

   * Target Python 3.13+ and PyGObject for GObject introspection.
   * Declare dependencies in `pyproject.toml` under `[tool.poetry.dependencies]`.

2. **Project Layout**

   * Place GNOME UI files in `data/ui/` and resources in `data/icons/`.

3. **Module & Naming Conventions**

   * Module files use `snake_case.py`.
   * Classes use `CamelCase`.
   * Signals and callbacks use `on_<widget>_<signal>()`.

4. **PEP 8 + Type Hints**

   * Follow PEP 8 line length (≤ 88 chars) and indentation (4 spaces).
   * Add type annotations for all public functions and methods.

5. **Gio.Application Pattern**

   * Subclass `Gio.Application` or `Gtk.Application`.
   * Override `do_activate()` to build UI and connect signals.

6. **UI & Logic Separation**

   * Load `.ui` files via `Gtk.Builder`.
   * Keep UI definitions in UI files; implement behavior in Python code.

7. **Signal Handling**

   * Use `builder.connect_signals(self)`; define handlers in the application class.
   * Return `True`/`False` appropriately for signal callbacks.

8. **Threading & Idle**

   * Offload long tasks to `threading.Thread`.
   * Use `GLib.idle_add()` to update UI from background threads.

9. **Error Handling**

   * Catch and handle `GLib.Error` for file I/O and D-Bus calls.
   * Log errors with `Gio.Logger.warning()` or `error()`.

10. **Resource Management**

* Use `Gio.resources_register()` for bundled assets.
* Avoid manual memory management; rely on GObject reference counting.

11. **Documentation**

* Add a docstring for every public class/function explaining purpose, parameters, and return types.
* Include desktop integration metadata (`.desktop` file) in `data/`.

12. **Testing**

* Structure tests under `tests/` mirroring `src/` layout.
* Use `pytest-gi` for testing GTK components and mock GObject signals.
* To run tests: `.venv/bin/pytest --maxfail=1 --disable-warnings -q`


