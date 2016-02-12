"""
This script is from https://github.com/kamillus/py2app-pyqt-codesign-fix-os-x
and slightly modified.
"""

import os
import re
import shutil

path_to_app = "dist/OnionShare.app"

def move_func(file):
    print("moving %s to %s " % (os.path.join(dir_name, file), os.path.join(dir_name, 'Versions', "Current")))
    try:
        shutil.move(os.path.join(dir_name, file), os.path.join(dir_name, 'Versions', "Current"))
    except Exception as e:
        print(e)
    return file

def filter_func(x):
    return x != "Versions"


dir = path_to_app + "/Contents/Frameworks/"
p = re.compile('^Qt(.+)\.framework$')

for dir_name, subdir_list, file_list in os.walk(dir):
    dir_name_short = dir_name.replace(dir, "")

    if p.match(dir_name_short):
        print('Found directory: %s' % dir_name_short)
        print(file_list)
        if os.path.islink(os.path.join(dir_name, file_list[0])):
            os.unlink(os.path.join(dir_name, file_list[0]))
        list(map(move_func, file_list[1:]))
        list(map(move_func, filter(filter_func, subdir_list)))
