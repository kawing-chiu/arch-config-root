#!/usr/bin/env python3
"""Generate a list of installed arch packages.

Use the following command to install from the generated
package list:

    cat /etc/installed_packages | pacman -S --needed -

"""
import subprocess

OUT_PKG_FILE = '/etc/installed_packages'


def main():
    args = _parse_args()
    with open(OUT_PKG_FILE, 'w') as f:
        p = subprocess.Popen(['pacman', '-Qqen'], stdout=f)
        p.wait()
    if args.local:
        with open(OUT_PKG_FILE + '_local', 'w') as f:
            p = subprocess.Popen(['pacman', '-Qqm'], stdout=f)
            p.wait()

def _parse_args():
    from argparse import ArgumentParser
    parser = ArgumentParser(description="")
    parser.add_argument('-l', '--local', action='store_true',
            help="also update non-official packages list")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()


