#!/usr/bin/env python3
"""Start ssh socks port forwarding to some vps.

Create configuration at ~/.vps-proxy manually before using
this script. The configuration format is like the following:

    [current]
    vps = vps1

    [vps1]
    host = 
    user = 
    password = 
    prompt = 

"""
import configparser
from time import sleep
from io import StringIO
from functools import partial
import sys
import os
import gc

import pexpect
import systemd.daemon


LOCAL_PORT = 8088
CONNECT_TIMEOUT = 20
TEST_TIMEOUT = 3

CONFIG_FILE = os.path.expanduser('~/.vps-proxy')


print_err = partial(print, file=sys.stderr, flush=True)
print = partial(print, flush=True)

def _sanitize(str_):
    out = StringIO()
    for c in str_:
        if c in '[].$':
            out.write('\\' + c)
        else:
            out.write(c)
    return out.getvalue()

def read_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    current_vps = config['current']['vps']
    vps_config = config[current_vps]
    vps_config['prompt'] = _sanitize(vps_config['prompt'])
    return vps_config

def start_tunnel(config):
    cmd = 'ssh -C -o ControlMaster=no -D {local_port} {user}@{host}'
    cmd = cmd.format(local_port=LOCAL_PORT,
        user=config['user'], host=config['host'])

    while True:
        print("Spawning tunnel...")
        ssh_tunnel = pexpect.spawnu(cmd, timeout=CONNECT_TIMEOUT)
        try:
            index = ssh_tunnel.expect([
                'password:',
                '\(yes/no\)',
                'Network is unreachable',
                pexpect.EOF])
            if index == 0:
                print("Authenticating...")
                ssh_tunnel.sendline(config['password'])
                print("Waiting for shell prompt...")
                ssh_tunnel.expect(config['prompt'])
                print("Tunnel ready.")
                return ssh_tunnel
            elif index == 1:
                sys.exit("Unknown host key. Please connect with {cmd} manually to "
                        "verify the fingerprint.".format(cmd=cmd))
            elif index == 2:
                print_err("Network is unreachable. Retry in 10s.")
                sleep(10)
            elif index == 3:
                print_err("Unexpected error:")
                print_err(ssh_tunnel.before.rstrip())
                print_err("Retry in 10s.")
                sleep(10)
        except pexpect.TIMEOUT:
            print_err("Timed out. Retry in 10s.")
            #print_err(ssh_tunnel.before.strip())
            sleep(10)
        finally:
            gc.collect()

def test_tunnel(ssh_tunnel, config):
    ssh_tunnel.sendline()
    try:
        ssh_tunnel.expect(config['prompt'], timeout=TEST_TIMEOUT)
        return True
    except pexpect.TIMEOUT:
        return False

def shutdown_tunnel(ssh_tunnel):
    ssh_tunnel.terminate(force=True)

def run():
    config = read_config()
    ssh_tunnel = start_tunnel(config)
    systemd.daemon.notify('READY=1')

    bad_count = 0
    while True:
        sleep(6)
        good = test_tunnel(ssh_tunnel, config)
        if not good:
            bad_count += 1
            print_err("Tunnel timed out. [count = {}]".format(bad_count))
            if bad_count > 2:
                print_err("Tunnel unresponsive, shutting down tunnel...")
                shutdown_tunnel(ssh_tunnel)
                ssh_tunnel = start_tunnel(config)
        else:
            bad_count = 0


if __name__ == '__main__':
    run()


