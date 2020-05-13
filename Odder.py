#!/usr/bin/env python3

import argparse
import os
import stat
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

"""


def doPatches(filepath, stockString, patchString, stringLine):
    # Bad patcher by Matty (@mosk_i)
    print("Patching", filepath, " at line", stringLine)
    if os.path.exists(filepath):
        with open(filepath, "rt") as f:
            data = f.readlines()
            if patchString in data[stringLine]:
                print("Patch already applied, Moving on to next patch...")
                return
            if stockString in data[stringLine]:
                data[stringLine] = str(patchString)
                f.close()
                g = open(filepath, "wt")
                g.writelines(data)
                g.close()
                # changing file permissions
                os.chmod(filepath, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
                         stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                return
            else:
                print("Didn't find '", stockString, "' in", filepath,
                      " at line ", stringLine, " Moving on to next patch...")
                return
    else:
        print("Couldn't find file at '", filepath,
              "'. Moving on to next patch...")
        return


def applyPatch():  # TODO Make it not replace the entire line, only what is specified
    doPatches("Makefile", "export SDK_PLATFORM	?=	iphoneos.internal",
              "export SDK_PLATFORM	?=	iphoneos\n", 36)
    doPatches("makefiles/config.mk", "DEPLOYMENT_TARGET_FLAGS	=	-mwatchos-version-min=$(SDKVERSION)",
              "DEPLOYMENT_TARGET_FLAGS	=	-mwatchos-version-min=10.0\n", 26)
    doPatches("makefiles/config.mk", "DEPLOYMENT_TARGET_FLAGS	=	-mtvos-version-min=$(SDKVERSION)",
              "DEPLOYMENT_TARGET_FLAGS	=	-mtvos-version-min==10.0\n", 29)
    doPatches("makefiles/config.mk", "DEPLOYMENT_TARGET_FLAGS	=	-miphoneos-version-min=$(SDKVERSION)",
              "DEPLOYMENT_TARGET_FLAGS	=	-miphoneos-version-min=10.0\n", 32)
    doPatches("drivers/flash_nand/ppn-swiss/ppn.c", r'			printf("nand_read_block_hook: failure %d reading block %u, count %zd\n", err, block, count);',
              r'			printf("nand_read_block_hook: failure %d reading block %u, count %u\n", err, block, count);' + "\n", 42)
    doPatches("lib/fs/fs.c", r"		memset((void *)addr, *maxsize, 0);",
              r"		memset((void *)addr, *maxsize, (0));" + "\n", 394)
    doPatches("makefiles/build.mk", "_RUNTIME_FLAGS		:=	-L$(SDKROOT)/usr/local/lib -lcompiler_rt-static $(LIBBUILTIN_BUILD)",
              "_RUNTIME_FLAGS		:=	-L$(SDKROOT)/usr/local/lib $(LIBBUILTIN_BUILD)\n", 24)
    # Following patch is optional. Feel free to uncomment it if you want to (Make sure you have img4 installed to /usr/local/bin/img4)
    #doPatches("tools/tools.mk", "export IMG4PAYLOAD	:=	$(shell xcrun -sdk $(SDKROOT) -find img4payload)", "export IMG4PAYLOAD	:=	/usr/local/bin/img4", 48)
    print("\nPatches are done!")
    pass


def build(application=None, device=None):

    clean()
    checkFiles()  # Always make sure that everything is good before we start

    if application == 'EmbeddedIOP':
        print('Making EmbeddedIOP...')
        subprocess.run(['make', 'APPLICATIONS=EmbeddedIOP'],
                       stdout=subprocess.PIPE)  # Device was passed

    elif application == 'iBoot':
        if device is not None:
            print('Making iBoot with device(s):', device)
            # Device was passed
            subprocess.run(['make', 'APPLICATIONS=iBoot',
                            f'TARGETS={device}'], stdout=subprocess.PIPE)
        else:
            sys.exit('No devices were passed!')

    elif application == 'SecureROM':
        print('Making SecureROM...')
        subprocess.run(['make', 'VERBOSE=YES', 'APPLICATIONS=SecureROM',
                        'IMAGE_FORMAT=img3'], stdout=subprocess.PIPE)

    else:
        sys.exit('Invaild application, got:', application)


def clean():
    if os.path.exists('build'):
        shutil.rmtree('build')


def checkFiles():
    # Provided from HomeDiagnostic
    device_map = '/usr/local/standalone/firmware/device_map.db'
    # Path for device_map.db
    xcode_path = '/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/usr/'
    # We need to make this so we can build (currently symlinked to local device_map.db)
    dirtomake = f'{xcode_path}local/standalone/firmware/'

    # Check if device_map.db exists

    if not os.path.exists(device_map):
        sys.exit(f'Did not find device_map.db at: {device_map}')

    # Check if we need to make the paths in Xcode

    if not os.path.exists(dirtomake):
        print(f'{dirtomake} does not exist, we have to grant sudo privileges here...')
        subprocess.run(["sudo", "mkdir", "-p", dirtomake],
                       stdout=subprocess.PIPE)

    # Check if device_map.db exits in Xcode path

    if not os.path.exists(f'{dirtomake}device_map.db'):
        print('Copying device_map.db to its necessary location in Xcode. We have to grant sudo privileges here...')
        subprocess.run(["sudo", "cp", "-rv", device_map,
                        f"{dirtomake}device_map.db"], stdout=subprocess.PIPE)


def devices():
    conn = sqlite3.connect('/usr/local/standalone/firmware/device_map.db')
    cursor = conn.cursor()
    # Returns all 32-bit devices :D
    thingy = cursor.execute(
        "SELECT DISTINCT TargetType ImageFormat FROM Targets WHERE ImageFormat in ('img3')")
    return ''.join([thingy])


def main():
    parser = argparse.ArgumentParser(usage=f"{sys.argv[0]} <option>")
    parser.add_argument(
        "--apply-patch", help="Apply patches from patchfile to enable compiling", action="store_true")
    parser.add_argument(
        "--build", help="Start the build process", action="store_true")
    parser.add_argument("--clean", help="Clean up", action="store_true")
    parser.add_argument(
        "--check", help="This will ensure you have all of the required files", action="store_true")
    parser.add_argument(
        "--devices", help="Get all of the supported devices", action="store_true")

    args = parser.parse_args()

    if args.apply_patch:
        applyPatch()

    elif args.build:
        targets = devices()  # Default, compile iBoot with all supported 32-bit devices
        build('iBoot', targets)

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
