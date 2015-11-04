#!/usr/bin/env python3
"""Restart network services.
"""
from subprocess import call


def _parse_args():
    from argparse import ArgumentParser
    parser = ArgumentParser(description="")
    args = parser.parse_args()
    return args

def run():
    args = _parse_args()

    print("Reconnecting wifi...")
    call(['systemctl', 'restart', 'netctl-auto@*'])
    print("Reloading unbound...")
    call(['unbound-control', 'reload'])
    #print("Restarting goagent...")
    #call(['systemctl', 'restart', 'goagent'])
    print("Restarting vps proxy...")
    call(['systemctl', 'restart', 'vps-proxy.service'])

if __name__ == '__main__':
    run()
