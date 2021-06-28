#!/bin/bash

vercomp () {
    if [[ $1 == $2 ]]
    then
        return 0
    fi
    local IFS=.
    local i ver1=($1) ver2=($2)
    # fill empty fields in ver1 with zeros
    for ((i=${#ver1[@]}; i<${#ver2[@]}; i++))
    do
        ver1[i]=0
    done
    for ((i=0; i<${#ver1[@]}; i++))
    do
        if [[ -z ${ver2[i]} ]]
        then
            # fill empty fields in ver2 with zeros
            ver2[i]=0
        fi
        if ((10#${ver1[i]} > 10#${ver2[i]}))
        then
            return 1
        fi
        if ((10#${ver1[i]} < 10#${ver2[i]}))
        then
            return 2
        fi
    done
    return 0
}

testvercomp () {
    vercomp $1 $2
    case $? in
        0) op='=';;
        1) op='>';;
        2) op='<';;
    esac
    if [[ $op != $3 ]]
    then
        # echo "FAIL: Expected '$3', Actual '$op', Arg1 '$1', Arg2 '$2'"
        return 0
    else
        # echo "Pass: '$1 $op $2'"
        return 1
    fi
}

meson setup builddir
cd builddir || { echo "Error: directory 'builddir' not found"; exit 1; }

mesonVersion=$(meson --version)
testvercomp $mesonVersion 0.55 '>'

if [ "$?" = 1 ]; then
    # Meson version > 0.55, so use the 'meson' command
    meson
    meson install
else
    # Meson version <= 0.55, so use the 'ninja' command
    ninja
    ninja install
fi


# Alternative code (for Debian / apt based distributions)
#import apt_pkg
#apt_pkg.init_system()
#
#a = '1:1.3.10-0.3'
#b = '1.3.4-1'
#vc = apt_pkg.version_compare(a,b)
#if vc > 0:
#    print('version a > version b')
#elif vc == 0:
#    print('version a == version b')
#elif vc < 0:
#    print('version a < version b')