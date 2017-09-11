#!/usr/bin/env bash
# This script should be run as user 'postgres'.

PG_DATA=/var/lib/postgres/data/

# Without the '-A md5' option, all local connections will be trusted.
# This command must be run locally.
initdb --locale en_US.UTF-8 -E UTF8 -A md5 -U postgres -W -D "$PG_DATA"


# After initializing, DB user can be created with:
#       createuser -h <host> -p <port> -U <user_name> --interactive -P

# After user creation, database can be created or dropped with:
#       createdb -h <host> -p <port> -U <user_name> <db_name>
#       dropdb -h <host> -p <port> -U <user_name> <db_name>

# To connect to to database:
#       psql -h <host> -p <port> -U <user_name> <db_name>
