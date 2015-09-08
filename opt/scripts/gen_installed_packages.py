#!/usr/bin/env python3
"""Generate a list of installed arch packages.
"""
import subprocess

OUT_PKG_FILE = '/etc/installed_packages'


def run():
    with open(OUT_PKG_FILE, 'w') as f:
        p = subprocess.Popen(['pacman', '-Qqen'], stdout=f)
        p.wait()
    with open(OUT_PKG_FILE + '_local', 'w') as f:
        p = subprocess.Popen(['pacman', '-Qqm'], stdout=f)
        p.wait()

if __name__ == "__main__":
    run()

