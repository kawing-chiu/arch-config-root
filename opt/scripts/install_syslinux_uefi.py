#!/usr/bin/env python3
"""Install syslinux to efi partition.
"""
import sys
import os
import subprocess
import shutil
import re


# target path inside EFI partition
TARGET_PATH = 'EFI/syslinux/'


def _get_device(path):
    df_out = subprocess.check_output(['df', '--output=source', path])
    df_out = df_out.decode().split('\n')
    assert df_out[0] == 'Filesystem', "There is something wrong with df's output."
    full_dev_path = df_out[1]

    print(full_dev_path)
    match = re.search(r'(/dev/[a-z]+)([1-9])', full_dev_path)
    return match.groups()


def copy_syslinux_files(path):
    if not os.path.exists(path):
        os.makedirs(path)
    if os.listdir(path):
        print("'{}' is not empty, do nothing.".format(path))
        sys.exit()

    print("Copying syslinux files to {}...".format(path))
    syslinux_files_dir = '/usr/lib/syslinux/efi64/'
    for file_ in os.listdir(syslinux_files_dir):
        shutil.copy(os.path.join(syslinux_files_dir, file_), path)

def set_efi_boot_entry(path):
    print("Creating EFI boot entry...")
    print("Current boot entries:")
    subprocess.call(['efibootmgr'])

    device, partition = _get_device(path)
    print("Adding new EFI boot entry...")
    subprocess.call(['efibootmgr', '-c', '-d', device, '-p', partition,
        '-l', os.path.join('/', TARGET_PATH, 'syslinux/syslinux.efi'),
        '-L', 'Syslinux'])

    print("New boot entries:")
    subprocess.call(['efibootmgr'])

def copy_boot_files(arch_path):
    if not os.path.exists(arch_path):
        os.makedirs(arch_path)

    print("Copying arch boot files to {}...".format(arch_path))
    for file_ in ['initramfs-linux.img', 'vmlinuz-linux']:
        shutil.copy(os.path.join('/boot/', file_), arch_path)

def create_syslinux_cfg(syslinux_path):
    cfg_file = os.path.join(syslinux_path, 'syslinux.cfg')
    cfg_template = """
    DEFAULT arch
    SAY Syslinux EFI now loading.....

    TIMEOUT 15
    PROMPT 1

    LABEL arch
        KERNRL ../arch/vmlinuz-linux
        APPEND ro cryptdevice=UUID= root= intel_iommu=on
        INITRD ../arch/initramfs-linux.img
    """

def _parse_args():
    from argparse import ArgumentParser
    parser = ArgumentParser(description="")
    parser.add_argument('mount_point', help="mount point of EFI partition, e.g. /boot/efi")
    args = parser.parse_args()
    if not os.path.ismount(args.mount_point):
        sys.exit("Error: '{}' is not a mount point".format(args.mount_point))
    return args

def run():
    args = _parse_args()

    path = os.path.join(args.mount_point, TARGET_PATH)
    syslinux_path = os.path.join(path, 'syslinux')
    arch_path = os.path.join(path, 'arch')

    copy_syslinux_files(syslinux_path)
    set_efi_boot_entry(path)
    copy_boot_files(arch_path)
    #create_syslinux_cfg(syslinux_path)


if __name__ == "__main__":
    run()

