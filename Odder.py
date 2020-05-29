#!/usr/bin/env python3

import argparse
import os
import shutil
import sqlite3
import stat
import subprocess
import sys


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

# TODO Update this


def doPatches(filepath, stockString, patchString, stringLine):
    # Bad patcher by Matty (@mosk_i)
    print("Patching {}\nat line {}".format(filepath, stringLine))
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
                print("Didn't find {}\nin\n{}\nat line\n{}\nMoving on to next patch...".format(
                    stockString, filepath, stringLine))
                return
    else:
        print("Couldn't find file at {}\nMoving on to next patch...".format(filepath))
        return


def applyPatch():  # TODO Make it not replace the entire line, only what is specified
    doPatches(
        "Makefile",
        "export SDK_PLATFORM	?=	iphoneos.internal",
        "export SDK_PLATFORM	?=	iphoneos\n",
        36)

    doPatches(
        "makefiles/config.mk",
        "DEPLOYMENT_TARGET_FLAGS	=	-mwatchos-version-min=$(SDKVERSION)",
        "DEPLOYMENT_TARGET_FLAGS	=	-mwatchos-version-min=10.0\n",
        26)

    doPatches(
        "makefiles/config.mk",
        "DEPLOYMENT_TARGET_FLAGS	=	-mtvos-version-min=$(SDKVERSION)",
        "DEPLOYMENT_TARGET_FLAGS	=	-mtvos-version-min==10.0\n",
        29)

    doPatches(
        "makefiles/config.mk",
        "DEPLOYMENT_TARGET_FLAGS	=	-miphoneos-version-min=$(SDKVERSION)",
        "DEPLOYMENT_TARGET_FLAGS	=	-miphoneos-version-min=10.0\n",
        32)

    doPatches(
        "drivers/flash_nand/ppn-swiss/ppn.c",
        r'			printf("nand_read_block_hook: failure %d reading block %u, count %zd\n", err, block, count);',
        r'			printf("nand_read_block_hook: failure %d reading block %u, count %u\n", err, block, count);' + "\n",
        42)

    doPatches(
        "lib/fs/fs.c",
        r"		memset((void *)addr, *maxsize, 0);",
        r"		memset((void *)addr, *maxsize, (0));" + "\n",
        394)

    doPatches(
        "makefiles/build.mk",
        "_RUNTIME_FLAGS		:=	-L$(SDKROOT)/usr/local/lib -lcompiler_rt-static $(LIBBUILTIN_BUILD)",
        "_RUNTIME_FLAGS		:=	-L$(SDKROOT)/usr/local/lib $(LIBBUILTIN_BUILD)\n",
        24)

    # Following patch is optional. Feel free to uncomment it if you want to (Make sure you have img4 installed to /usr/local/bin/img4)
    # doPatches(
    # "tools/tools.mk",
    #"export IMG4PAYLOAD	:=	$(shell xcrun -sdk $(SDKROOT) -find img4payload)",
    #"export IMG4PAYLOAD	:=	/usr/local/bin/img4",
    # 48)


def build(application=None, device=None):

    clean()
    checkFiles()  # Always make sure that everything is good before we start

    if application == 'EmbeddedIOP':
        print('Making EmbeddedIOP...')
        subprocess.run([
            'make',
            'APPLICATIONS=EmbeddedIOP'],
            stdout=subprocess.PIPE)

    elif application == 'iBoot':
        if device is not None:
            print('Making iBoot with device(s):', device)
            subprocess.run([
                'make',
                'APPLICATIONS=iBoot',
                'TARGETS={}'.format(device)],
                stdout=subprocess.PIPE)
        else:
            sys.exit('No devices were passed!')

    elif application == 'SecureROM':
        print('Making SecureROM...')
        subprocess.run([
            'make',
            'VERBOSE=YES',
            'APPLICATIONS=SecureROM',
            'IMAGE_FORMAT=img3'],
            stdout=subprocess.PIPE)

    else:
        raise ValueError('Invaild application, got:', application)


def clean():
    if os.path.exists('build'):
        shutil.rmtree('build')


def checkFiles():
    # Provided from HomeDiagnostic
    try:
        device_map = '/usr/local/standalone/firmware/device_map.db'
        os.path.exists(device_map)
    except:
        raise FileNotFoundError

    # Path for device_map.db
    xcode_path = '/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/usr/'

    # We need to make this so we can build
    dirtomake = '{}local/standalone/firmware/'.format(xcode_path)

    # Check if device_map.db exists

    if not os.path.exists(device_map):
        raise FileNotFoundError(
            'Did not find device_map.db at: {}'.format(device_map))

    # Check if we need to make the paths in Xcode

    if not os.path.exists(dirtomake):
        print('{} does not exist, we have to grant sudo privileges here...'.format(
            dirtomake))
        subprocess.run([
            "sudo",
            "mkdir",
            "-p",
            dirtomake],
            stdout=subprocess.PIPE)

    # Check if device_map.db exits in Xcode path

    if not os.path.exists('{}device_map.db'.format(dirtomake)):
        print('Copying device_map.db to its necessary location in Xcode. We have to grant sudo privileges here...')
        subprocess.run([
            "sudo",
            "cp",
            "-rv",
            device_map,
            "{}device_map.db".format(dirtomake)],
            stdout=subprocess.PIPE)


def devices():
    conn = sqlite3.connect('/usr/local/standalone/firmware/device_map.db')
    cursor = conn.cursor()
    # Returns all 32-bit devices :D
    thingy = cursor.execute(
        "SELECT DISTINCT TargetType ImageFormat FROM Targets WHERE ImageFormat in ('img3')")
    return ''.join([thingy])


def main():
    argv = sys.argv
    parser = argparse.ArgumentParser(usage="{} <option>".format(argv[0]))
    parser.add_argument(
        "--apply-patch", help="Apply patches from patchfile to enable compiling", action="store_true")
    parser.add_argument(
        "--build", help="Start the build process", action="store_true")
    parser.add_argument(
        "--clean", help="Clean up", action="store_true")
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
