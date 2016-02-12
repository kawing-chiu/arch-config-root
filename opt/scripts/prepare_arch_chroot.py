#!/usr/bin/env python3
"""Prepare a directory for arch chroot.
"""
import sys
import os
import subprocess
from subprocess import Popen
import shutil

from _utils import *
from bootstrap_new_arch_system import ADMIN_USER_NAME


ROOT_FILE_LIST = [
    '~/.gitconfig',
    '~/.vps-proxy',
    '~/.mykeyfile',
    '~/.ssh/id_rsa',
    '~/.ssh/id_rsa.pub',
    '/opt/dicts/',
    '/usr/share/fonts/Win8/',
]

USER_FILE_LIST = [
    '~/.mozilla',
    '~/.config/chromium',
]


def pacstrap(target_dir):
    print("Running pacstrap...")
    run(['pacstrap', target_dir, 'base', 'vim', 'git', 'openssh', 'python', 'bash-completion'])

def _copy_to_dir(target_dir, file_):
    file_ = os.path.abspath(os.path.expanduser(file_))
    print("\tcopying {}".format(file_))
    if not os.path.exists(file_):
        print("\tWARNING: {} does not exist".format(file_))
        return
    if not os.path.isdir(file_):
        dir_, base = os.path.split(file_)
        new_dir = target_dir + dir_
        print("\tto: {}".format(new_dir))
        os.makedirs(new_dir, exist_ok=True)
        return shutil.copy(file_, new_dir)
    else:
        dir_ = file_
        new_dir = target_dir + dir_
        print("\tto: {}".format(new_dir))
        return shutil.copytree(file_, new_dir, symlinks=True)

def copy_root_files(target_dir, file_list):
    print("Copying files...")
    for file_ in file_list:
        _copy_to_dir(target_dir, file_)

def copy_user_files(target_dir, file_list):
    print("Copying user files...")
    for file_ in file_list:
        call_f_as_user(ADMIN_USER_NAME, _copy_to_dir, (target_dir, file_))

def gen_fstab(target_dir):
    print("Generating fstab...")
    out_fstab = target_dir + '/etc/fstab'
    with open(out_fstab, 'ab') as f:
        p = Popen(['genfstab', '-p', '/mnt'], stdout=f)
        p.communicate()

def chroot(target_dir):
    print("Chrooting...")
    #os.execvp('arch-chroot', ['arch-chroot', target_dir, '/bin/bash'])
    run(['arch-chroot', target_dir, '/bin/bash'])

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
    copy_root_files(target_dir, ROOT_FILE_LIST)
    get_config(target_dir)
    chroot(target_dir)
    copy_user_files(target_dir, USER_FILE_LIST)


if __name__ == '__main__':
    main()
