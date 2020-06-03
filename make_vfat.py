#!/usr/bin/env python3
# encoding: utf-8
#
#    make_vfat.py - create vfat drive image based on a directory
#    Copyright (C) 2020 Falk Garbsch
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import argparse
import json
import subprocess
import tempfile
import shutil
import time
import sys

def prefix_sparse(offset, input, output):
    '''
    Prefixes the input file with a given number of bytes and writes it to the
    given output file.
    
    The sparse holes of the input file will be copied to the output file
    automatically.
    '''
    print("  open(r) %s" % (input))
    fin = os.open(input, os.O_RDONLY)

    print("  open(w) %s" % (output))
    fout = os.open(output, os.O_WRONLY | os.O_CREAT, 0o644)
    size = os.lseek(fin, 0, os.SEEK_END)
    os.ftruncate(fout, size + offset)

    buffersize = 1024 * 1024 * 64
    blocksize = 0
    start = 0
    try:
        while True:
            start = os.lseek(fin, start, os.SEEK_DATA)
            end = os.lseek(fin, start, os.SEEK_HOLE)
            os.lseek(fin, start, os.SEEK_SET)

            sys.stdout.write("  copy %10d - %10d " % (start, end))
            os.lseek(fout, start + offset, os.SEEK_SET)
            size = end - start
            missing = size
            buffer = [0]
            while size > 0:
                length = size
                if length > buffersize:
                    size -= buffersize
                    length = buffersize
                else:
                    size = 0
                buffer = os.read(fin, length)
                missing -= os.write(fout, buffer)
                sys.stdout.write("#")

            sys.stdout.write("\n")
            if missing > 0:
                print("ERROR:  skipped %d bytes on write written" % (missing))
            start = end
    except:
        pass

    os.close(fin)
    os.close(fout)
  
def main(args, tmp):
    blocksize = 1048576  # 1mb
    part1 = os.path.join(tmp, "part1.img")

    if os.path.exists(args.output):
        if not args.force:
            print("ERROR: output file already exists")
            return
        print("\ndelete %s..." % (args.output))
        os.remove(args.output)

    size = int(args.size) - 1  # decrease by 1 mb for partition header
    print("\ncreating image file...")
    fp = os.open(part1, os.O_WRONLY | os.O_CREAT, 0o644)
    os.ftruncate(fp, blocksize * size)
    os.close(fp)

    print("\ncreating filesystem...")
    command = [ "mkfs.vfat", "-n", args.label, part1 ]
    subprocess.check_call(command)

    print("\ncopy files...")
    basedir = os.path.abspath(os.path.join(args.source, "files"))
    entries = [os.path.join(basedir, x) for x in os.listdir(basedir)]
    command = [ "mcopy", "-i", part1, "-s", "-v" ] + entries + [ "::", ]
    subprocess.check_call(command)

    print("\ncopy file and make room for partition table...")
    prefix_sparse(blocksize, part1, args.output)

    print("creating partition table...")
    command = [ "sfdisk", args.output ]
    proc = subprocess.Popen(command, stdin = subprocess.PIPE)
    proc.communicate(b",,c;\n")
    proc.wait()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Creates an image containing a vfat partition containing files from a specified directory.")
    parser.add_argument("source", type=str, help="Input directory containing the configuration and root tree.")
    parser.add_argument("output", type=str, help="The image file to be written.")
    parser.add_argument("--size", type=int, default=31744, help="Size for the disk image in MB. (default: 31744)")
    parser.add_argument("--label", type=str, default="vfat", help="Label for the fat partition created. (default: vfat)")
    parser.add_argument("--force", default=False, action='store_true', help="Force to overwrite an existing output file")
    try:
        tmp = tempfile.mkdtemp("_make_vfat")
        main(parser.parse_args(), tmp)
    finally:
        print("cleanup %s..." % (tmp))
        shutil.rmtree(tmp)
