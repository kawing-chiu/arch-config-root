#!/usr/bin/env python3
"""Install syslinux to efi partition.

This script should be run *inside of* chroot.
"""
import sys
import os
import subprocess
import shutil
import re

from _utils import *

# TODO: clean up the code, it's too ugly


# target path inside EFI partition
USB_MODE_PATH = 'EFI/BOOT/'

BIOS_PATH = 'bios_boot/'
ARCH_PATH = 'arch_linux/'


def _get_partition_by_path(path):
    df_out = subprocess.check_output(['df', '--output=source', path])
    df_out = df_out.decode().split('\n')
    assert df_out[0] == 'Filesystem', "There is something wrong with df's output."
    full_dev_path = df_out[1]

    return full_dev_path


def copy_syslinux_uefi_files(target_path):
    print("Copying syslinux uefi files to {}...".format(target_path))
    if not os.path.exists(target_path):
        os.makedirs(target_path)

    syslinux_files_dir = '/usr/lib/syslinux/efi64/'
    for file_ in os.listdir(syslinux_files_dir):
        shutil.copy(os.path.join(syslinux_files_dir, file_), target_path)

    old_efi_bin = os.path.join(target_path, 'syslinux.efi')
    new_efi_bin = os.path.join(target_path, 'bootx64.efi')
    print("\trename {} to {}".format(old_efi_bin, new_efi_bin))
    shutil.move(old_efi_bin, new_efi_bin)

def copy_syslinux_bios_files(target_path):
    print("Copying syslinux bios files to {}...".format(target_path))
    if not os.path.exists(target_path):
        os.makedirs(target_path)

    syslinux_files_dir = '/usr/lib/syslinux/bios/'
    for file_ in os.listdir(syslinux_files_dir):
        if file_.endswith('.c32'):
            shutil.copy(os.path.join(syslinux_files_dir, file_), target_path)

def copy_arch_boot_files(target_path):
    if not os.path.exists(target_path):
        os.makedirs(target_path)

    print("Copying arch boot files to {}...".format(target_path))
    for file_ in ['initramfs-linux.img', 'vmlinuz-linux']:
        shutil.copy(os.path.join('/boot/', file_), target_path)

#def set_efi_boot_entry(path):
#    print("Creating EFI boot entry...")
#    print("Current boot entries:")
#    subprocess.call(['efibootmgr'])
#
#    full_dev_path = _get_partition_by_path(path)
#    match = re.search(r'(/dev/[a-z]+)([1-9])', full_dev_path)
#    device, partition = match.groups()
#
#    print("Adding new EFI boot entry...")
#    subprocess.call(['efibootmgr', '-c', '-d', device, '-p', partition,
#        '-l', os.path.join('/', PC_MODE_PATH, 'syslinux/syslinux.efi'),
#        '-L', 'Syslinux'])
#
#    print("New boot entries:")
#    subprocess.call(['efibootmgr'])

def create_syslinux_cfg(syslinux_path, arch_path, crypt_path, crypt_name, type_):
    print("Generating syslinux config...")
    cfg_template = """
    DEFAULT arch
    SAY Syslinux {type} now loading......

    TIMEOUT 15
    PROMPT 1

    LABEL arch
        KERNEL {rel_path}/vmlinuz-linux
        APPEND rw cryptdevice=UUID={crypt_uuid}:{crypt_name} root={root_part} intel_iommu=on
        INITRD {rel_path}/initramfs-linux.img
    """

    crypt_uuid = subprocess.check_output(['blkid', '-s', 'UUID', '-o', 'value', crypt_path])
    crypt_uuid = crypt_uuid.rstrip().decode()
    rel_path = os.path.relpath(arch_path, start=syslinux_path)
    root_part = _get_partition_by_path('/')

    config = cfg_template.format(crypt_uuid=crypt_uuid,
            crypt_name=crypt_name, root_part=root_part,
            rel_path=rel_path, type=type_)
    lines = config.splitlines()
    lines = map(lambda x: x[4:], lines)
    config = '\n'.join(lines)

    cfg_file = os.path.join(syslinux_path, 'syslinux.cfg')
    with open(cfg_file, 'w') as f:
        print("\tcreate syslinux UEFI config file {}".format(cfg_file))
        f.write(config)

def install_syslinux_uefi(arch_path, syslinux_uefi_path, crypt_path, crypt_name):
    copy_syslinux_uefi_files(syslinux_uefi_path)
    copy_arch_boot_files(arch_path)
    create_syslinux_cfg(syslinux_uefi_path, arch_path, crypt_path, crypt_name, 'UEFI')

def install_syslinux_bios(arch_path, syslinux_bios_path, device, part_num, crypt_path, crypt_name):
    copy_syslinux_bios_files(syslinux_bios_path)
    print("Installing syslinux to {}, path: {}".format(device, BIOS_PATH))
    # due to a mtools bug, the following does not work
    #partition = device + part_num
    #cmd = ['syslinux', '-i', '-d', BIOS_PATH, partition]
    # this seems working
    cmd = ['extlinux', '-i', syslinux_bios_path]
    print("\tcommand line: {}".format(cmd))
    run(cmd)

    print("Writing MBR...")
    mbr_bin_file = '/usr/lib/syslinux/bios/gptmbr_c.bin'
    run(['dd', 'bs=440', 'count=1', 'conv=notrunc',
        'if=' + mbr_bin_file, 'of=' + device])

    print("Setting bootflag...")
    # use 'sgdisk -A list' to show all setable attributes
    # show set attributes on partition: 'sgdisk -A <part_num>:show <device>'
    run(['sgdisk', '--attributes=' + part_num + ':set:2', device])
    print("\tcheck with 'sgdisk -A {}:show {}'".format(part_num, device))

    create_syslinux_cfg(syslinux_bios_path, arch_path, crypt_path, crypt_name, 'BIOS')

def _test_paths(paths):
    print("Checking installation paths...")
    for path in paths:
        if os.path.exists(path) and os.listdir(path):
            print("Directory '{}' is not empty. Exiting.".format(path))
            sys.exit()

def _parse_args():
    from argparse import ArgumentParser
    parser = ArgumentParser(description="")
    parser.add_argument('mount_point', default='/boot/efi', nargs='?',
            help="mount point of EFI partition, e.g. /boot/efi")
    parser.add_argument('-u', '--update', action='store_true',
            help="update kernel only")
    args = parser.parse_args()

    if not os.path.ismount(args.mount_point):
        sys.exit("Error: '{}' is not a mount point".format(args.mount_point))

    return args

def main():
    args = _parse_args()
    mount_point = args.mount_point

    partition = _get_partition_by_path(mount_point)
    device = partition[:-1]
    part_num = partition[-1]
    if args.update:
        print("Updating the kernel in '{}', device: {}, partition num: {}".format(
            mount_point, device, part_num))
    else:
        print("Installing syslinux to '{}', device: {}, partition num: {}".format(
            mount_point, device, part_num))

    syslinux_uefi_path = os.path.join(mount_point, USB_MODE_PATH)
    print("\tsyslinux_uefi_path: {}".format(syslinux_uefi_path))
    syslinux_bios_path = os.path.join(mount_point, BIOS_PATH)
    print("\tsyslinux_bios_path: {}".format(syslinux_bios_path))
    arch_path = os.path.join(mount_point, ARCH_PATH)
    print("\tarch_path: {}".format(arch_path))

    confirm = input("Check the above information and confirm (type uppercase yes): ")
    if confirm != 'YES':
        sys.exit()

    #_test_paths([syslinux_uefi_path, syslinux_bios_path])
    if args.update:
        copy_arch_boot_files(arch_path)
    else:
        crypt_path = input("Input the path of the encrypted partition, "
                "i.e. /dev/sda3: ").strip()
        crypt_name = input("The name of the crypt device, i.e. luks_on_sdxc: ")

        install_syslinux_uefi(arch_path, syslinux_uefi_path, crypt_path, crypt_name)
        install_syslinux_bios(arch_path, syslinux_bios_path, device, part_num, crypt_path, crypt_name)

    run(['sync'])

    print("Done.")


if __name__ == "__main__":
    main()

