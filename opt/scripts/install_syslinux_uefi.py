#!/usr/bin/env python3
"""Install syslinux to efi partition.

This script should be run *inside of* chroot.
"""
import sys
import os
import subprocess
import shutil
import re


# target path inside EFI partition
PC_MODE_PATH = 'EFI/syslinux/'
USB_MODE_PATH = 'EFI/BOOT/'

BIOS_PATH = 'syslinux_bios/'
ARCH_PATH = 'arch/'


def _get_device(path):
    df_out = subprocess.check_output(['df', '--output=source', path])
    df_out = df_out.decode().split('\n')
    assert df_out[0] == 'Filesystem', "There is something wrong with df's output."
    full_dev_path = df_out[1]

    return full_dev_path


def copy_uefi_syslinux_files(target_path, mode):
    print("Copying syslinux files to {}...".format(target_path))
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    if os.listdir(target_path):
        print("Directory '{}' is not empty. Exiting.".format(target_path))
        sys.exit()

    syslinux_files_dir = '/usr/lib/syslinux/efi64/'
    for file_ in os.listdir(syslinux_files_dir):
        shutil.copy(os.path.join(syslinux_files_dir, file_), target_path)

    if mode == 'usb':
        old_efi_bin = os.path.join(target_path, 'syslinux.efi')
        new_efi_bin = os.path.join(target_path, 'bootx64.efi')
        print("\trename {} to {}".format(old_efi_bin, new_efi_bin))
        shutil.move(old_efi_bin, new_efi_bin)

def copy_arch_boot_files(target_path):
    if not os.path.exists(target_path):
        os.makedirs(target_path)

    print("Copying arch boot files to {}...".format(target_path))
    for file_ in ['initramfs-linux.img', 'vmlinuz-linux']:
        shutil.copy(os.path.join('/boot/', file_), target_path)

def set_efi_boot_entry(path):
    print("Creating EFI boot entry...")
    print("Current boot entries:")
    subprocess.call(['efibootmgr'])

    full_dev_path = _get_device(path)
    match = re.search(r'(/dev/[a-z]+)([1-9])', full_dev_path)
    device, partition = match.groups()

    print("Adding new EFI boot entry...")
    subprocess.call(['efibootmgr', '-c', '-d', device, '-p', partition,
        '-l', os.path.join('/', PC_MODE_PATH, 'syslinux/syslinux.efi'),
        '-L', 'Syslinux'])

    print("New boot entries:")
    subprocess.call(['efibootmgr'])

def create_syslinux_cfg(syslinux_path, arch_path):
    print("Generating syslinux config...")
    cfg_template = """
    DEFAULT arch
    SAY Syslinux UEFI now loading......

    TIMEOUT 15
    PROMPT 1

    LABEL arch
        KERNEL {rel_path}/vmlinuz-linux
        APPEND ro cryptdevice=UUID={crypt_uuid}:{crypt_name} root={root_path} intel_iommu=on
        INITRD {rel_path}/initramfs-linux.img
    """

    crypt_path = input("Please input the path of the encrypted partition, "
            "i.e. /dev/sda3: ").strip()
    crypt_uuid = subprocess.check_output(['blkid', '-s', 'UUID', '-o', 'value', crypt_path])
    crypt_uuid = crypt_uuid.rstrip().decode()
    crypt_name = input("The name of the crypt device, i.e. luks_on_sdxc: ")
    rel_path = os.path.relpath(arch_path, start=syslinux_path)
    root_path = _get_device('/')

    config = cfg_template.format(crypt_uuid=crypt_uuid,
            crypt_name=crypt_name, root_path=root_path, rel_path=rel_path)
    lines = config.splitlines()
    lines = map(lambda x: x[4:], lines)
    config = '\n'.join(lines)

    cfg_file = os.path.join(syslinux_path, 'syslinux.cfg')
    with open(cfg_file, 'w') as f:
        print("\tcreate syslinux UEFI config file {}".format(cfg_file))
        f.write(config)

def _parse_args():
    from argparse import ArgumentParser
    parser = ArgumentParser(description="")
    parser.add_argument('mount_point', default='/boot/efi', nargs='?',
            help="mount point of EFI partition, e.g. /boot/efi")
    parser.add_argument('-m', '--mode', choices=['pc', 'usb'], default='usb',
            help="update kernel only without installing syslinux")
    parser.add_argument('-u', '--update-kernel-only', action='store_true',
            help="update kernel only without installing syslinux")
    args = parser.parse_args()

    if not os.path.ismount(args.mount_point):
        sys.exit("Error: '{}' is not a mount point".format(args.mount_point))

    return args

def run():
    args = _parse_args()
    mode = args.mode
    mount_point = args.mount_point

    dev = _get_device(mount_point)
    print("Installing syslinux to '{}'...".format(dev))

    if mode == 'usb':
        # install to usb removable media
        syslinux_uefi_path = os.path.join(mount_point, USB_MODE_PATH)
        copy_uefi_syslinux_files(syslinux_uefi_path, mode)

        arch_path = os.path.join(mount_point, ARCH_PATH)
        copy_arch_boot_files(arch_path)
        create_syslinux_cfg(syslinux_uefi_path, arch_path)

    #base_path = os.path.join(args.mount_point, PC_MODE_PATH)
    #syslinux_path = os.path.join(base_path, 'syslinux')
    #arch_path = os.path.join(base_path, 'arch')

    #if args.update_kernel_only:
    #    copy_boot_files(arch_path)
    #else:
    #    copy_syslinux_files(syslinux_path)
    #    set_efi_boot_entry(path)
    #    copy_boot_files(arch_path)
    #    create_syslinux_cfg(syslinux_path)

    print("Done.")


if __name__ == "__main__":
    run()

