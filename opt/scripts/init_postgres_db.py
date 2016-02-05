#!/usr/bin/env python3
"""Initialize a new postgres database."""
import os
import sys

from _utils import *


def main():
    path = input("Path of the new database: ")
    cmd = ['initdb', '--locale', 'en_US.UTF-8', '-E', 'UTF8', '-D', path]

    is_root = os.geteuid() == 0
    if is_root:
        user = input("Create database as user: ")
        if user == 'root':
            sys.exit("Error: please don't create database as root.")
        run_as_user(user, cmd)
    else:
        run(cmd)

if __name__ == "__main__":
    main()
