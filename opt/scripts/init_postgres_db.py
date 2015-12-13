#!/usr/bin/env python3
"""Initialize a new postgres database."""
import os
import sys

from _utils import *


def run():
    path = input("Path of the new database: ")
    cmd = ['initdb', '--locale', 'en_US.UTF-8', '-E', 'UTF8', '-D', path]

    is_root = os.geteuid() == 0
    if is_root:
        user = input("Create database as user: ")
        if user == 'root':
            sys.exit("Error: please don't create database as root.")
        call_as_user(user, cmd)
    else:
        call(cmd)

if __name__ == "__main__":
    run()
