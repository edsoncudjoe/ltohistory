#!/usr/bin/env python3
# This tool organises files into a given directory to be
# written to LTO tape. Ensuring the directory does not exceed
# the size of 1.3TB.
# This tool can be called from the command line as shown in
# the example below
# Example:
# $ ./assign_lto_tape.py --source <SOURCE_DIR> --destination <TARGET_DIR>
#

import argparse
import os
import shutil

__author__ = "Edson Cudjoe"
__copyright__ = "Copyright 2019, Intervideo Ltd"
__credits__ = ["Edson Cudjoe"]
__license__ = "MIT"
__version__ = "1.0.0"
__maintainer__ = "Edson Cudjoe"
__email__ = "it@intervide.co.uk"
__status__ = "Beta"

p = argparse.ArgumentParser()
p.add_argument('-s', "--source", type=str, required=True,
               help="Enter the working directory")
p.add_argument('-t', "--destination", type=str, required=True,
               help="Enter the LTO folder the files need to be moved to")
args = p.parse_args()

def size_fmt(num, suffix='B'):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
        
def move_files_to_lto_dir(source, destination):
    target_dir_size_limit = 1319413953331
    
    target_dir_curr_size = 0
    for path, dirs, names in os.walk(source):
        for n in names:
            if not n.startswith('.'):
                try:
                    filesize = os.path.getsize(os.path.join(path, n))
                    target_dir_curr_size += filesize
                    shutil.move(os.path.join(path, n), destination)
                    if target_dir_curr_size < target_dir_size_limit:
                        continue
                    else:
                        print('Tape capacity reached.')
                        print('Target dir size: {}'.format(size_fmt(target_dir_curr_size)))
                        return False
                except shutil.Error as shellerr:
                    print(shellerr)
                    continue
                except OSError as oserr:
                    print(oserr)
                    continue
    print('Complete')
    final = size_fmt(target_dir_curr_size)
    print('Target dir size: {}'.format(final))

working_dir = args.source
target_dir = args.destination
move_files_to_lto_dir(working_dir, target_dir)

