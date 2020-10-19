#!/bin/bash

pushd src &> /dev/null
if [ $? -ne 0 ]; then
    echo "Missing source directory."
    exit 1
fi
make clean
make
if [ $? -ne 0 ]; then
    echo "Could not build Sentinel source code."
    exit 1
fi
sudo make install
if [ $? -ne 0 ]; then
    echo "Could not install Sentinel source code."
    exit 1
fi

popd &> /dev/null

wget "https://ftp.postgresql.org/pub/source/v9.6.13/postgresql-9.6.13.tar.bz2"
if [ $? -ne 0 ]; then
    echo "Could not download postgres 9.6.13 source code!"
    exit 1
fi

tar xjf postgresql-9.6.13.tar.bz2
if [ $? -ne 0 ]; then
    echo "Could not untar postgres source code."
    exit 1
fi

cp pg_diff.diff postgresql-9.6.13
if [ $? -ne 0 ]; then
    echo "Could not copy PG diff to PG dir."
    exit 1
fi

pushd postgresql-9.6.13 &> /dev/null


./configure
if [ $? -ne 0 ]; then
    echo "Could not configure postgresql."
    exit 1
fi

patch -p1 < pg_diff.diff
if [ $? -ne 0 ]; then
    echo "Could not apply postresql patch."
    exit 1
fi

make
if [ $? -ne 0 ]; then
    echo "Could not build postgresql."
    exit 1
fi

sudo make install
if [ $? -ne 0 ]; then
    echo "Could not install postgresql."
    exit 1
fi

popd &>/dev/null

/usr/local/pgsql/bin/pg_ctl --version
