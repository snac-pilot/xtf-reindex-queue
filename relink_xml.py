#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pprint import pprint as pp
import sys
import os
import re
import scandir

# each file needs to be in its own directory
BASE1 = u'/home/ec2-user/merge'
BASE2 = u'/home/ec2-user/merge2'


def main(argv=None):
    # find all the files in the directory
    for dir_entry in scandir.scandir(BASE1):
        if dir_entry.is_file:
            subdir, hardlink = s3_key_to_fullpath(dir_entry.name)
            linksource = os.path.join(BASE1, dir_entry.name)
            create_link(subdir, linksource, hardlink)


def s3_key_to_fullpath(name):
    ark_name = os.path.splitext(name)[0]
    subdir = os.path.join(BASE2,
                          ark_name[-2:],
                          ark_name)
    fullpath = os.path.join(BASE2,
                            subdir,
                            name)
    return subdir, fullpath


def create_link(subdir, linksource, hardlink):
    if not(os.path.isfile(hardlink)):
        _mkdir(subdir)
        os.link(linksource, hardlink)
        print subdir, linksource, hardlink


# http://code.activestate.com/recipes/82465-a-friendly-mkdir/
def _mkdir(newdir):
    """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
    """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired " \
                      "dir, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            _mkdir(head)
        #print "_mkdir %s" % repr(newdir)
        if tail:
            os.mkdir(newdir)


if __name__ == "__main__":
    sys.exit(main())
