# rilato

A description of this project.

## Development

### Install Dependencies

**System packages**
```bash
# Debian/Ubuntu
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 ninja-build meson python3-pip
# Fedora
sudo dnf install python3-gobject python3-cairo gobject-introspection-devel gtk4-devel libadwaita-devel meson ninja-build python3-pip
```

**Python & project**
```bash
pip3 install poetry
poetry install
```

### Git Hooks Setup
```bash
# Install pre-commit hooks
poetry run pre-commit install

# Install pre-push hook
cp git-hooks/pre-push .git/hooks/
chmod +x .git/hooks/pre-push
```

The pre-commit hooks will run automatically on commit and will:
- Run ruff check with auto-fix
- Run ruff format

The pre-push hook will run automatically on push and will:
- Run pytest to ensure all tests pass

### Build & Run
```bash
poetry run rilato-build
poetry run rilato
