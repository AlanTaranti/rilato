#!/usr/bin/env python3
import subprocess
import os


def main():
    root = os.getcwd()
    prefix = os.path.join(root, "build")
    cmds = [
        [
            "meson",
            "setup",
            "build",
            f"--prefix={prefix}",
            "--buildtype=debug",
            "--reconfigure",
        ],
        ["meson", "compile", "-C", "build"],
    ]
    for cmd in cmds:
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)


def run():
    """Run the built rilato binary."""
    script = os.path.join(os.getcwd(), "build", "bin", "rilato")
    print(f"Running: {script}")
    subprocess.run([script], check=True)
