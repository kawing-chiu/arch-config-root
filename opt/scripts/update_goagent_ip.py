#!/usr/bin/env python3
"""Update /etc/goagent with new ips.
"""
import fileinput
import re
import shutil
import sys
import select

NEW_IP_FILE = '/home/statistician/opt/search_google_ip/good_ips'
GOAGENT_CONFIG_FILE = '/etc/goagent'


def load_ips_from_file():
    with open(NEW_IP_FILE) as f:
        ips = f.readline().rstrip()
    return ips

def replace_old_ips(new_ips):
    for line in fileinput.input(files=GOAGENT_CONFIG_FILE, inplace=True, backup='.bak'):
        line = line.rstrip()
        if re.search(r'google_cn|google_hk|google_talk', line):
            line = re.sub(r'= ?.*$', '= ' + new_ips, line)
        print(line)

def run():
    from_stdin = select.select([sys.stdin], [], [], 0)[0]
    if from_stdin:
        new_ips = sys.stdin.readline().rstrip()
    else:
        new_ips = load_ips_from_file()
    replace_old_ips(new_ips)
    shutil.chown(GOAGENT_CONFIG_FILE, group='nobody')
    print("{} updated from {}.".format(
        GOAGENT_CONFIG_FILE,
        "stdin" if from_stdin else NEW_IP_FILE
    ))

if __name__ == "__main__":
    run()

