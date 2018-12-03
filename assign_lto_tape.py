import argparse
import os
import shutil

# add files to directory.
# ensure size of directory does not exceed designated size

working_dir = '' # Enter working dir
target_dir = '' # Enter target dir

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

move_files_to_lto_dir(working_dir, target_dir)

