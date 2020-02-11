#!/usr/bin/env python3

import argparse
import os
import sqlite3
import subprocess
import sys
import shutil


"""

In order to install HomeDiagnostic, you have to disable SIP. Enter recovery and enter csrutil disable.

Devices supported out-of-the-box: (13F40)
    940:
        iPhone 4S
            n94
        iPad 2
            k93, k94, k95
    942:
        iPad 2
            k93a
        iPod Touch 5th Gen
            n78
        AppleTV 3rd Gen
            j33
        iPad Mini
            p105, p106, p107
    945:
        iPad 3rd Gen
            j1, j2, j2a
    947:
        AppleTV 3rd Gen
            j33i
    950:
        iPhone 5
            n41, n42
        iPhone 5C
            n48, n49
    955:
        iPad 4G
            p101, p102, p103
            
64-bit cannot be built (without reversing)
        
brew cask install db-browser-for-sqlite (This is to view the contents of device_map.db)

TODO: 

    - Build SecureROM (if possible)

    - Better patching process

"""
# -----------------
"""
Patching process:
    - ./Makefile [line 37] // iphoneos.internal > iphoneos [./Makefile line 37]
    - ./tools/generate_debug_hashes.py // chmod +x 
    - ./tools/check_liblist.py // chmod +x
    - ./makefiles/config.mk [line 27, 30, 33] // $SDKVERSION -> 10.0
    - ./drivers/flash_nand/ppn-swiss/ppn.c [line 43] // count %zd\n -> count %u\n
    - ./lib/fs/fs.c [line 395] // memset((void *)addr, *maxsize, 0); -> memset((void *)addr, *maxsize, (0));
    - ./makefiles/build.mk [line 25] // Remove -lcompiler_rt-static
    - ./tools/macho_post_process.py // chmod +x
Optional:
    - ./tools/tools.mk [line 49] // /usr/local/bin/img4 (if you somehow are 1337 h4^X0r, this is useful)
"""


def applyPatch(): # TODO Either add some code to change, or make a better patch file or similar
    #subprocess.run(['git', 'apply', '--verbose', 'patchfile'], stdout=subprocess.PIPE)
    # If you can somehow use the provided patchfile (not from git diff this time)
    pass


def build(application=None, device=None):

    clean()
    checkFiles() # Always make sure that everything is good before we start

    if application == 'EmbeddedIOP':
        print('Making EmbeddedIOP...')
        subprocess.run(['make', 'APPLICATIONS=EmbeddedIOP'], stdout=subprocess.PIPE) # Device was passed

    elif application == 'iBoot':
        if device is not None:
            print('Making iBoot with device(s):', device)
            subprocess.run(['make', 'APPLICATIONS=iBoot', f'TARGETS={device}'], stdout=subprocess.PIPE) # Device was passed
        else:
            sys.exit('No devices were passed!')

    elif application == 'SecureROM':
        print('Making SecureROM...')
        subprocess.run(['make', 'VERBOSE=YES', 'APPLICATIONS=SecureROM', 'IMAGE_FORMAT=img3'], stdout=subprocess.PIPE)

    else:
        sys.exit('Invaild application, got:', application)


def clean():
    if os.path.exists('build'):
        shutil.rmtree('build')


def checkFiles():
    device_map = '/usr/local/standalone/firmware/device_map.db'  # Provided from HomeDiagnostic
    xcode_path = '/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/usr/'  # Path for device_map.db
    dirtomake = f'{xcode_path}local/standalone/firmware/'  # We need to make this so we can build (currently symlinked to local device_map.db)

    # Check if device_map.db exists

    if not os.path.exists(device_map):
        sys.exit(f'Did not find device_map.db at: {device_map}')

    # Check if we need to make the paths in Xcode

    if not os.path.exists(dirtomake):
        print(f'{dirtomake} does not exist, we have to grant sudo privileges here...')
        subprocess.run(["sudo", "mkdir", "-p", dirtomake], stdout=subprocess.PIPE)
    
    # Check if device_map.db exits in Xcode path

    if not os.path.exists(f'{dirtomake}device_map.db'):
        print('Copying device_map.db to its necessary location in Xcode. We have to grant sudo privileges here...')
        subprocess.run(["sudo", "cp", "-rv", device_map, f"{dirtomake}device_map.db"], stdout=subprocess.PIPE)


def convertListToSingleString(data):
    devices = ''

    # TODO I'm sure there's a more simple and obviously better choice of code, fix?
    for target in data:
        shit = ''.join(target)
        devices += " " + shit
    return devices.strip()


def devices(): 
    conn = sqlite3.connect('/usr/local/standalone/firmware/device_map.db')
    cursor = conn.cursor()
    thingy = cursor.execute("SELECT DISTINCT TargetType ImageFormat FROM Targets WHERE ImageFormat in ('img3')") # Returns all 32-bit devices :D
    return convertListToSingleString(thingy)


def main():
    parser = argparse.ArgumentParser(usage=f"{sys.argv[0]} <option>")
    parser.add_argument("--apply-patch", help="Apply patches from patchfile to enable compiling", action="store_true")
    parser.add_argument("--build", help="Start the build process", action="store_true")
    parser.add_argument("--clean", help="Clean up", action="store_true")
    parser.add_argument("--check", help="This will ensure you have all of the required files", action="store_true")
    parser.add_argument("--devices", help="Get all of the supported devices", action="store_true")

    args = parser.parse_args()

    if args.apply_patch:
        #applyPatch()
        print('View the code of this script, it has all of the info provided to apply the patches')

    elif args.build:
        #targets = devices() # Default, compile iBoot with all supported 32-bit devices
        build('iBoot', 'n94')

    elif args.clean:
        clean()

    elif args.check:
        checkFiles()

    elif args.devices:
        print(devices())

    else:
        sys.exit(parser.print_help(sys.stderr))


if __name__ == '__main__':
   main() 

"""
Road to compiling the only provided 32-bit ROM, with weird (to me) directories:
    drivers/apple/aes_v2/aes_v2.h:16:10: fatal error: 'soc/t8002/b0/module/aes.h' file not found
    ./drivers/samsung/aes/aes.h
    ./include/drivers/aes.h
    ./platform/t8002/include/platform/soc/spds/aes.h
    socgen
    ./platform/t8002/b0
    ./platform/s8000/include/platform/soc/s8000/b0
    ./platform/s8000/include/platform/soc/s8001/b0
    platform/s8000/include/platform/soc/s8000/b0
    make VERBOSE=YES APPLICATIONS=SecureROM TARGETS=t8002 IMAGE_FORMAT=img3
"""
