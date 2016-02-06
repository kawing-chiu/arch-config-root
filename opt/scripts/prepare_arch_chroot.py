#!/usr/bin/env python3
"""Prepare a directory for arch chroot.
"""
import sys
import os
import subprocess
from subprocess import Popen
import shutil

from _utils import *


COPY_FILE_LIST = [
    '~/.gitconfig',
    '~/.vps-proxy',
    '~/.ssh/id_rsa',
    '~/.ssh/id_rsa.pub',
    '/opt/dicts/',
    '/usr/share/fonts/Win8/',
]


def pacstrap(target_dir):
    print("Running pacstrap...")
    run(['pacstrap', target_dir, 'base', 'vim', 'git', 'openssh', 'python', 'bash-completion'])

def copy_files(target_dir):
    print("Copying files...")
    for file_ in COPY_FILE_LIST:
        file_ = os.path.abspath(os.path.expanduser(file_))
        print('\tcopying {}'.format(file_))
        if not os.path.isdir(file_):
            dir_, base = os.path.split(file_)
            new_dir = target_dir + dir_
            print('\tto: {}'.format(new_dir))
            os.makedirs(new_dir, exist_ok=True)
            shutil.copy(file_, new_dir)
        else:
            dir_ = file_
            new_dir = target_dir + dir_
            print('\tto: {}'.format(new_dir))
            shutil.copytree(file_, new_dir)

def gen_fstab(target_dir):
    print("Generating fstab...")
    out_fstab = target_dir + '/etc/fstab'
    with open(out_fstab, 'ab') as f:
        p = Popen(['genfstab', '-p', '/mnt'], stdout=f)
        p.communicate()

def chroot(target_dir):
    print("Chrooting...")
    os.execvp('arch-chroot', ['arch-chroot', target_dir, '/bin/bash'])

def get_config(target_dir):
    print("Loading system configs from github...")

    old_cwd = os.getcwd()
    os.chdir(target_dir)

    run(['git', 'init'])
    run(['git', 'remote', 'add', 'origin',
        'git@github.com:kawing-chiu/arch-config-root.git'])
    run(['git', 'fetch'])
    run(['git', 'checkout', '-t', '-f', 'origin/master'])

    os.chdir(old_cwd)

def _parse_args():
    from argparse import ArgumentParser
    parser = ArgumentParser(description="")
    parser.add_argument('target_dir')
    args = parser.parse_args()
    return args

def main():
    args = _parse_args()
    target_dir = os.path.abspath(args.target_dir)

    pacstrap(target_dir)
    gen_fstab(target_dir)
    copy_files(target_dir)
    get_config(target_dir)
    chroot(target_dir)


if __name__ == '__main__':
    main()
