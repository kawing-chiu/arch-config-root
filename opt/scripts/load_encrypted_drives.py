#!/usr/bin/env python3
"""Load encrypted external hard drives.
"""
import sys
import os
import subprocess
from time import sleep


KNOWN_DRIVES = {
    'FTD': {
        'UUID': '72c48928-bc01-416c-b19b-86f305ef5235',
        'LUKS_NAME': 'luks-on-freecom-toughdrive',
        'LVM_NAME': 'FTD',
    },
    'transcend': {
        'UUID': '01c1f7f3-8e5c-40b7-a742-733c4a464302',
        'LUKS_NAME': 'luks-on-transcend-storejet',
        'LVM_NAME': 'lvm-on-transcend-storejet',
    }
}


def load_drive(drive):
    print("Unlocking encrypted device...")
    cmdline = ['cryptsetup', '-v', '-d', '/root/.mykeyfile','luksOpen',
            'UUID=' + drive['UUID'], drive['LUKS_NAME']]
    subprocess.call(cmdline)
    sleep(0.3)
    print("Activating lvm volume group...")
    subprocess.call(['vgchange', '-a', 'y', drive['LVM_NAME']])

def unload_drive(drive):
    print("Deactivating lvm volume group...")
    subprocess.call(['vgchange', '-a', 'n', drive['LVM_NAME']])
    print("Closing encrypted device...")
    subprocess.call(['cryptsetup', '-v', 'luksClose', drive['LUKS_NAME']])

def _parse_args():
    from argparse import ArgumentParser
    parser = ArgumentParser(description="")
    parser.add_argument('action', choices=['load', 'unload'])
    parser.add_argument('drive')
    args = parser.parse_args()
    return args

def run():
    args = _parse_args()
    if args.drive not in KNOWN_DRIVES:
        sys.exit("Unknown drive {}.".format(args.drive))
    drive = KNOWN_DRIVES[args.drive]
    action = args.action

    map_path = os.path.join('/dev/mapper/', drive['LUKS_NAME'])
    if action == 'load':
        if os.path.exists(map_path):
            print("Drive '{}' already loaded.".format(args.drive))
            return
        load_drive(drive)

    elif action == 'unload':
        if not os.path.exists(map_path):
            print("Drive '{}' not loaded.".format(args.drive))
            return
        unload_drive(drive)


if __name__ == "__main__":
    run()

