#!/bin/bash

platform='unknown'
unamestr=`uname`
if [[ "$unamestr" == 'Linux' ]]; then
   platform='linux'
elif [[ "$unamestr" == 'FreeBSD' ]]; then
   platform='freebsd'
elif [[ "$unamestr" == 'Darwin' ]]; then
   platform='macOS'
fi

echo $unamestr

if [[ "$platform" == 'macOS' ]]; then
    sudo route delete -net 192.168.21.0/24 192.168.20.254
    sudo route delete -net 192.168.22.0/24 192.168.20.254
    sudo route delete -net 192.168.23.0/24 192.168.20.254
    sudo route delete -net 192.168.24.0/24 192.168.20.254
    sudo route delete -net 192.168.11.0/24 192.168.10.254
    sudo route delete -net 192.168.12.0/24 192.168.10.254
    sudo route delete -net 192.168.13.0/24 192.168.10.254
    sudo route delete -net 192.168.14.0/24 192.168.10.254


    sudo route add -net 192.168.21.0/24 192.168.20.254
    sudo route add -net 192.168.22.0/24 192.168.20.254
    sudo route add -net 192.168.23.0/24 192.168.20.254
    sudo route add -net 192.168.24.0/24 192.168.20.254
    sudo route add -net 192.168.11.0/24 192.168.10.254
    sudo route add -net 192.168.12.0/24 192.168.10.254
    sudo route add -net 192.168.13.0/24 192.168.10.254
    sudo route add -net 192.168.14.0/24 192.168.10.254
elif [[ "$platform" == 'linux' ]]; then
    sudo route delete -net 192.168.21.0/24 gw 192.168.20.254
    sudo route delete -net 192.168.22.0/24 gw 192.168.20.254
    sudo route delete -net 192.168.23.0/24 gw 192.168.20.254
    sudo route delete -net 192.168.24.0/24 gw 192.168.20.254
    sudo route delete -net 192.168.11.0/24 gw 192.168.10.254
    sudo route delete -net 192.168.12.0/24 gw 192.168.10.254
    sudo route delete -net 192.168.13.0/24 gw 192.168.10.254
    sudo route delete -net 192.168.14.0/24 gw 192.168.10.254


    sudo route add -net 192.168.21.0/24 gw 192.168.20.254
    sudo route add -net 192.168.22.0/24 gw 192.168.20.254
    sudo route add -net 192.168.23.0/24 gw 192.168.20.254
    sudo route add -net 192.168.24.0/24 gw 192.168.20.254
    sudo route add -net 192.168.11.0/24 gw 192.168.10.254
    sudo route add -net 192.168.12.0/24 gw 192.168.10.254
    sudo route add -net 192.168.13.0/24 gw 192.168.10.254
    sudo route add -net 192.168.14.0/24 gw 192.168.10.254
else
    echo Unsupported platform
fi
