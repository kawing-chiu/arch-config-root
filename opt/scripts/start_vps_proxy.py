#!/usr/bin/env python3
"""Start ssh socks port forwarding to some vps.
"""
import configparser
from time import sleep
from io import StringIO
from functools import partial
import sys
import os

import pexpect
import systemd.daemon


LOCAL_PORT = 8088
TIMEOUT = 3

CONFIG_FILE = os.path.expanduser('~/.vps-proxy')
PROFILE = 'myvps'


print_err = partial(print, file=sys.stderr)

def _sanitize(str_):
    out = StringIO()
    for c in str_:
        if c in '.$':
            out.write('\\' + c)
        else:
            out.write(c)
    return out.getvalue()

def read_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    config = config[PROFILE]
    config['prompt'] = _sanitize(config['prompt'])
    return config

def start_tunnel(config):
    cmd = 'ssh -C -o ControlMaster=no -D {local_port} {user}@{host}'
    cmd = cmd.format(local_port=LOCAL_PORT,
        user=config['user'], host=config['host'])
    print("Spawning tunnel...")
    ssh_tunnel = pexpect.spawnu(cmd)
    print("Waiting for password prompt...")
    index = ssh_tunnel.expect(['password:', '\(yes/no\)'])
    if index == 0:
        ssh_tunnel.sendline(config['password'])
        print("Waiting for shell prompt...")
        ssh_tunnel.expect(config['prompt'])
        return ssh_tunnel
    elif index == 1:
        sys.exit("Unknown host key. Please connect with {cmd} manually to "
                "verify the fingerprint.".format(cmd=cmd))

def test_tunnel(ssh_tunnel, config):
    ssh_tunnel.sendline()
    try:
        ssh_tunnel.expect(config['prompt'], timeout=TIMEOUT)
        return True
    except pexpect.TIMEOUT:
        return False

def shutdown_tunnel(ssh_tunnel):
    print("Shutting down tunnel...")
    ssh_tunnel.terminate(force=True)

def run():
    config = read_config()
    ssh_tunnel = start_tunnel(config)
    systemd.daemon.notify('READY=1')
    print("Tunnel ready.")

    bad_count = 0
    while True:
        sleep(10)
        good = test_tunnel(ssh_tunnel, config)
        if not good:
            bad_count += 1
            print_err("Tunnel timed out.")
            if bad_count > 3:
                shutdown_tunnel(ssh_tunnel)
                ssh_tunnel = start_tunnel(config)
        else:
            bad_count = 0


if __name__ == '__main__':
    run()


