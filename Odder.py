#!/usr/bin/env python3

import argparse
import os
import sqlite3
import sys

"""

In order to install WhiteTails, you have to disable SIP. Enter recovery and enter csrutil disable.

Devices supported out-of-the-box:
    950:
        iPhone 5
            n41, n42
        iPhone 5C
            n48, n49
    955:
        iPad 4G
            p101, p102, p103
            
64-bit cannot be built
        
brew cask install db-browser-for-sqlite (This is to view the contents of device_map.db)

TODO: 

    - Build SecureROM

    - Add missing data to build EmbeddedIOP for other devices (only builds for a few as of now)
    
    - Print all of supported devices (data: Target, TargetType, Platform, ChipID, SecurityEpoch, CryptoHashMethod,
    ProductID, ImageFormat) Check with makefiles/device_map.mk
    
    - Hack up some janky Python code to add custom devices
    
    - Figure out how to parse args like this: ./Odder.py --build --device n41

"""


def applyPatch():
    os.system('git apply patchfile')


def build():
    application = ['iBoot', 'SecureROM', 'EmbeddedIOP']  # SecureROM is not working
    devices_all = 'n41 n42 n48 n49 p101 p102 p103'  # Working out of the box. 950 and 955 devices.

    print(f'Building iBoot for device(s): {devices_all}!')
    os.system(f'make APPLICATIONS="iBoot" TARGETS="{devices_all}"')


def clean():
    if os.path.exists('build'):
        print('Cleaning up!')
        os.system('make clean')
    else:
        print('build folder not found, not cleaning!')


def checkFiles():
    device_map = '/usr/local/standalone/firmware/device_map.db'  # Provided from HomeDiagnostic
    xcode_path = '/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/usr/'  # Path for device_map.db
    dirtomake = f'{xcode_path}local/standalone/firmware/'  # We need to make this so we can build

    # Check if device_map.db exists

    if os.path.exists(device_map):
        print(f'{device_map} exists!')
    else:
        sys.exit(f'Did not find device_map.db at: {device_map}')

    # Check if we need to make the paths in Xcode

    if os.path.exists(dirtomake):
        print(f'{dirtomake} exists!')
    else:
        print(f'{dirtomake} does not exist, we have to grant sudo privileges here...')
        os.system(f'sudo mkdir -p {dirtomake}')

    # Check if device_map.db exits in Xcode path

    if os.path.exists(f'{dirtomake}device_map.db'):
        print(f'{dirtomake}device_map.db exists!')
    else:
        print('Copying device_map.db to its necessary location in Xcode. We have to grant sudo privileges here...')
        os.system(f'sudo cp -rv {device_map} {dirtomake}device_map.db')


def test():
    conn = sqlite3.connect('device_map.db')
    cursor = conn.cursor()
    cursor.execute('SELECT Target FROM Targets')
    devices = cursor.fetchall()
    print(devices)


if __name__ == '__main__':
    argv = sys.argv
    argc = len(argv)

    parser = argparse.ArgumentParser()
    # parser.add_argument("--add", help="Add device to device_map database", action="store_true")
    parser.add_argument("--apply-patch", help="Apply patches from patchfile to enable compiling", action="store_true")
    parser.add_argument("--build", help="Start the build process", action="store_true")
    parser.add_argument("--clean", help="Clean up", action="store_true")
    parser.add_argument("--check", help="This will ensure you have all of the required files", action="store_true")
    # parser.add_argument("--device", help="Compile with the given device(s)", action="store_true")
    parser.add_argument("--devices", help="Get all of the supported devices", action="store_true")
    # parser.add_argument("--EmbeddedIOP", help="Compile EmbeddedIOP only", action="store_true")
    # parser.add_argument("--iBoot", help="Compile iBoot only", action="store_true")
    # parser.add_argument("--SecureROM", help="Compile SecureROM only", action="store_true")

    args = parser.parse_args()

    if args.apply_patch:
        applyPatch()

    elif args.build:
        clean()
        checkFiles()
        build()

    elif args.clean:
        clean()

    elif args.check:
        checkFiles()

    elif args.devices:
        test()

    else:
        sys.exit(parser.print_help())
