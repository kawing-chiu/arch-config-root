#!/usr/bin/env python3
"""Config a new arch system inside chroot.

This script should be run inside a chroot, after the
following steps:

    pacstrap /mnt base vim-python3 git openssh
    arch-chroot /mnt /bin/bash
    cd /
    git init
    git remote add origin git@github.com:kawing-chiu/arch-config-root.git
    git fetch
    git checkout -t -f origin/master

After running this script, there are some steps remaining:

    create a network profile in /etc/netctl
    configure boot-loader
    edit /etc/fstab and /etc/crypttab

"""
import sys
import os
import subprocess
from subprocess import Popen, PIPE


PACKAGES_LIST_FILE = '/etc/installed_packages'
ADMIN_USER_NAME = 'statistician'
SPECIAL_SYSTEM_GROUPS = ['raise_nofile_limit']


def install_packages():
    print("Installing packages...")
    with open(PACKAGES_LIST_FILE, 'rb') as f:
        packages = f.read()
    p = Popen(['pacman', '-S', '--needed', '-'], stdin=PIPE)
    p.communicate(input=packages)

def set_host_name():
    print("Setting hostname...")
    host_name = input("Input hostname: ")
    with open('/etc/hostname', 'w') as f:
        print(host_name, file=f)

def set_time_zone():
    print("Setting time zone...")
    os.symlink('/usr/share/zoneinfo/Asia/Shanghai', '/etc/localtime')

def gen_locales():
    print("Generating locales...")
    subprocess.call(['locale-gen'])

def make_initramfs():
    print("Generating initramfs...")
    subprocess.call(['mkinitcpio', '-p', 'linux'])

def change_root_password():
    print("Setting root password...")
    subprocess.call(['passwd'])

def add_special_groups():
    print("Adding special groups...")
    for group in SPECIAL_SYSTEM_GROUPS:
        subprocess.call(['groupadd', '--system', group])

def create_admin_user():
    print("Creating admin user {}...".format(ADMIN_USER_NAME))
    subprocess.call(['useradd', '-m', '-U', '-s', '/bin/bash'])
    add_to_groups_cmdline = ['gpasswd', '-a', ADMIN_USER_NAME, 'wheel'] + \
            SPECIAL_SYSTEM_GROUPS
    subprocess.call(add_to_groups_cmdline)
    print("Setting password for {}...".format(ADMIN_USER_NAME))
    subprocess.call(['passwd', ADMIN_USER_NAME])

def run():
    install_packages()
    set_host_name()
    set_time_zone()
    gen_locales()
    make_initramfs()
    change_root_password()
    add_special_groups()
    create_admin_user()

    print("Done.")

if __name__ == "__main__":
    run()

