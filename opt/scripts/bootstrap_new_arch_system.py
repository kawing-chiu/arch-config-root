#!/usr/bin/env python3
"""Config a new arch system inside chroot.

This script should be run inside a chroot, after the
following steps:

    pacstrap /mnt base vim-python3 git openssh
    genfstab -p /mnt >> /mnt/etc/fstab

    (copy ssh keys into /mnt/root/.ssh)

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

"""
import sys
import os
import subprocess
from subprocess import Popen, PIPE
import pwd
import shutil


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

def unbound_setup():
    print("Setting up unbound-control...")
    subprocess.call(['unbound-control-setup'])

def change_root_password():
    print("Setting root password...")
    subprocess.call(['passwd'])

def add_special_groups():
    print("Adding special groups...")
    for group in SPECIAL_SYSTEM_GROUPS:
        subprocess.call(['groupadd', '--system', group])

def create_admin_user():
    print("Creating admin user {}...".format(ADMIN_USER_NAME))
    subprocess.call(['useradd', '-m', '-U', '-s', '/bin/bash',
        ADMIN_USER_NAME])

    groups = ['wheel'] + SPECIAL_SYSTEM_GROUPS
    for group in groups:
        subprocess.call(['gpasswd', '-a', ADMIN_USER_NAME, group])

    print("Setting password for {}...".format(ADMIN_USER_NAME))
    subprocess.call(['passwd', ADMIN_USER_NAME])

def get_user_config():
    user_record = pwd.getpwnam(ADMIN_USER_NAME)
    user_name = user_record.pw_name
    user_dir = user_record.pw_dir
    uid = user_record.pw_uid
    gid = user_record.pw_gid

    env = os.environ.copy()
    env['HOME'] = user_dir
    env['LOGNAME'] = user_name
    env['USER'] = user_name
    env['PWD'] = user_dir

    def change_user():
        os.setgroups([])
        os.setgid(gid)
        os.setuid(uid)

    def call_as_user(cmd):
        subprocess.call(cmd, cwd=user_dir, env=env,
            preexec_fn=change_user)

    ssh_dir = os.path.join(user_dir, '.ssh')
    if not os.path.exists(ssh_dir):
        os.mkdir(ssh_dir, 0o700)
        shutil.chown(ssh_dir, uid, gid)
    for file_ in ['id_rsa', 'id_rsa.pub']:
        src = os.path.join('/root/.ssh', file_)
        dest = os.path.join(ssh_dir, file_)
        shutil.copy(src, dest)
        shutil.chown(dest, uid, gid)

    call_as_user(['git', 'init'])
    call_as_user(['git', 'remote', 'add', 'origin',
        'https://github.com/kawing-chiu/arch-config-home.git'])
    call_as_user(['git', 'fetch'])
    call_as_user(['git', 'checkout', '-t', '-f', 'origin/master'])

    call_as_user(['git', 'clone', '--recursive',
        'https://github.com/kawing-chiu/dotvim.git', '.vim'])

    call_as_user(['git', 'clone',
        'https://github.com/kawing-chiu/exc.git', 'exercises'])

def run():
    #install_packages()
    #set_host_name()
    #set_time_zone()
    #gen_locales()
    #make_initramfs()
    #unbound_setup()

    #change_root_password()
    #add_special_groups()
    #create_admin_user()
    get_user_config()

    print("Done.")

if __name__ == "__main__":
    run()

