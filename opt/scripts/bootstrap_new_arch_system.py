#!/usr/bin/env python3
"""Config a new arch system inside chroot.

This script should be run inside a chroot, after the
following steps:

    pacstrap /mnt base vim git openssh
    genfstab -p /mnt >> /mnt/etc/fstab

    copy ssh keys, windows fonts, dicts to the new root

    arch-chroot /mnt /bin/bash

    git config --global user.email 'kawing.chiu.sysu@gmail.com'
    git config --global user.name 'Zhao Jiarong'
    git config --global push.default simple

    cd /
    git init
    git remote add origin git@github.com:kawing-chiu/arch-config-root.git
    git fetch
    git checkout -t -f origin/master

    (the above steps may be moved to a script in the future)

After running this script, there are some steps remaining:

    create a network profile in /etc/netctl
    configure boot-loader
    edit /etc/fstab and /etc/crypttab
    copy .mozilla, .config/chromium folders
    install non-official packages

"""
import sys
import os
import subprocess
from subprocess import Popen, PIPE
import pwd
import grp
import shutil
from io import StringIO

from _utils import *


PACKAGES_LIST_FILE = '/etc/installed_packages'
ADMIN_USER_NAME = 'statistician'
ADMIN_SYSTEM_GROUPS = ['wheel', 'raise_nofile_limit']


def install_packages():
    print("Installing packages...")
    with open(PACKAGES_LIST_FILE, 'rb') as f:
        packages = f.read()
    p = Popen(['pacman', '-Syu', '--needed', '-'], stdin=PIPE)
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
    run(['locale-gen'])

def make_initramfs():
    print("Generating initramfs...")
    run(['mkinitcpio', '-p', 'linux'])

def unbound_setup():
    print("Setting up unbound-control...")
    run(['unbound-control-setup'])

#def goagent_setup():
#    print("Setting up goagent...")
#    os.symlink('/usr/share/goagent/local/CA.crt',
#        '/etc/ca-certificates/trust-source/anchors/goagent.crt')
#    subprocess.call(['trust', 'extract-compat'])
#
#    config_template = """
#    [gae]
#    appid =
#    password =
#    
#    [iplist]
#    google_cn =
#    
#    google_hk =
#    
#    google_talk =
#    
#    [dns]
#    enable = 0
#    listen = 127.0.0.1:5353
#    """
#    lines = config_template.split('\n')
#    lines = map(lambda x: x[4:], lines)
#    config_template = '\n'.join(lines)
#    with open('/etc/goagent', 'w') as f:
#        f.write(config_template)

def change_root_password():
    print("Setting root password...")
    run(['passwd'])

def add_special_groups():
    print("Adding special groups...")
    for group in ADMIN_SYSTEM_GROUPS:
        try:
            grp.getgrnam(group)
        except KeyError:
            print("\tadding group {}".format(group))
            run(['groupadd', '--system', group])

def create_admin_user():
    print("Creating admin user {}...".format(ADMIN_USER_NAME))
    run(['useradd', '-m', '-U', '-s', '/bin/bash',
        ADMIN_USER_NAME])

    for group in ADMIN_SYSTEM_GROUPS:
        run(['gpasswd', '-a', ADMIN_USER_NAME, group])

    print("Setting password for {}...".format(ADMIN_USER_NAME))
    run(['passwd', ADMIN_USER_NAME])

def copy_ssh_keys():
    user_record = pwd.getpwnam(ADMIN_USER_NAME)
    user_name = user_record.pw_name
    user_dir = user_record.pw_dir
    uid = user_record.pw_uid
    gid = user_record.pw_gid

    ssh_dir = os.path.join(user_dir, '.ssh')
    if not os.path.exists(ssh_dir):
        os.mkdir(ssh_dir, 0o700)
        shutil.chown(ssh_dir, uid, gid)
    for file_ in ['id_rsa', 'id_rsa.pub']:
        src = os.path.join('/root/.ssh', file_)
        dest = os.path.join(ssh_dir, file_)
        shutil.copy(src, dest)
        shutil.chown(dest, uid, gid)


def get_user_config():
    print("Loading user configs from github...")

    copy_ssh_keys()

    run_as_user(ADMIN_USER_NAME, ['git', 'init'])
    run_as_user(ADMIN_USER_NAME, ['git', 'remote', 'add', 'origin',
        'git@github.com:kawing-chiu/arch-config-home.git'])
    run_as_user(ADMIN_USER_NAME, ['git', 'fetch'])
    run_as_user(ADMIN_USER_NAME, ['git', 'checkout', '-t', '-f', 'origin/master'])

    run_as_user(ADMIN_USER_NAME, ['git', 'clone', '--recursive',
        'git@github.com:kawing-chiu/dotvim.git', '.vim'])

    run_as_user(ADMIN_USER_NAME, ['git', 'clone',
        'git@github.com:kawing-chiu/exc.git', 'exercises'])

def create_efi_mount_point():
    efi_dir = '/boot/efi'
    print("Creating EFI mount point: {}".format(efi_dir))
    os.makedirs(efi_dir, exist_ok=True)

def note():
    print("Note that this script does not install a bootloader. "
            "To install syslinux, run install_syslinux.py manually "
            "*inside* this chroot")

def main():
    install_packages()
    set_host_name()
    set_time_zone()
    gen_locales()
    make_initramfs()

    # currently, unbound-control-setup has a serious bug
    #unbound_setup()

    #goagent_setup()

    change_root_password()
    add_special_groups()
    create_admin_user()
    get_user_config()

    create_efi_mount_point()
    note()

    print("Done.")

if __name__ == "__main__":
    main()

