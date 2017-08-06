#!/usr/bin/env python3
"""Prepare a directory for arch chroot.

Before using this script, the disk should be partitioned and properly set up
using cryptsetup and lvm. Some commands for reference:

    cryptsetup luksFormat <partition>
    cryptsetup luksOpen <partition> <crypt_mapper_name>
    pvcreate -v <crypt_mapper>
    vgcreate -v <vg_name> <crypt_mapper>
    lvcreate -v -n <lv_name> -L/-l <size> <vg_name>
    mkfs.ext4 -v /dev/<vg_name>/<lv_name>

"""
import sys
import os
import subprocess
from subprocess import Popen
import shutil

from _utils import *
from bootstrap_new_arch_system import DEFAULT_ADMIN_USER


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

# a relative path should be used
SWAP_FILE = 'swapfile'


def pacstrap(target_dir):
    print("Running pacstrap...")
    # TODO: consider installing more packages here so that we can save the time
    # downloading the packages inside the chroot
    pkgs = ['base', 'base-devel', 'vim', 'git', 'openssh', 'python',
            'bash-completion', 'xorg', 'clang', 'vlc', 'firefox', 'chromium',
            'archlinux-keyring']
    # '-c' means to use the package cache on the host
    #run(['pacstrap', '-c', target_dir, *pkgs])
    run(['pacstrap', '-G', target_dir, *pkgs])

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
        call_f_as_user(DEFAULT_ADMIN_USER, _copy_to_dir, (target_dir, file_))

def gen_fstab(target_dir):
    print("Generating fstab...")
    out_fstab = target_dir + '/etc/fstab'
    with open(out_fstab, 'ab') as f:
        p = Popen(['genfstab', '-p', target_dir], stdout=f)
        p.communicate()

def chroot(target_dir):
    print("Chrooting...")
    #os.execvp('arch-chroot', ['arch-chroot', target_dir, '/bin/bash'])
    run(['arch-chroot', target_dir, '/bin/bash'])

def get_config(target_dir):
    print("Loading system configs from github...")

    input("Press any key to continue...")

    old_cwd = os.getcwd()
    os.chdir(target_dir)

    run(['git', 'init'])
    run(['git', 'remote', 'add', 'origin',
        'git@github.com:kawing-chiu/arch-config-root.git'])
    run(['git', 'fetch'])
    run(['git', 'checkout', '-t', '-f', 'origin/master'])

    os.chdir(old_cwd)

def create_swap_file(target_dir):
    print("Creating swap file...")
    size = input("The size of the swap file: ")
    swap_file = os.path.join(target_dir, SWAP_FILE)
    run(['fallocate', '-l', size, swap_file])
    run(['chmod', '600', swap_file])
    run(['mkswap', swap_file])

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
    create_swap_file(target_dir)
    chroot(target_dir)
    copy_user_files(target_dir, USER_FILE_LIST)

    print("Done.")


if __name__ == '__main__':
    main()
