#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pprint import pprint as pp
import sys
import os
import re
import argparse
import urlparse
import boto
import re
import subprocess


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'bucket',
        nargs=1,
        help="s3://bucket[/optional/path] where the EAC XML are"
    )
    parser.add_argument('local_dir', nargs=1)
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin)
    parser.add_argument('--pull_all', dest='all', action='store_true')

    if argv is None:
        argv = parser.parse_args()

    # open the bucket with the EAC-CPF
    parts = urlparse.urlsplit(argv.bucket[0])
    # SplitResult
    # (scheme='s3', netloc='test.pdf', path='/dkd', query='', fragment='')
    s3 = boto.connect_s3()
    bucket = s3.get_bucket(parts.netloc)

    if argv.all:
        pull_all(bucket, argv.bucket[0], argv.local_dir[0])
        reindex_xtf()
    else:
        # look for ARKs in the infile (one per line)
        todo = []
        for line in argv.infile:
            info = get_info(argv.bucket[0], argv.local_dir[0], line.strip("\n"))
            if info:
                key_name = os.path.join(parts.path, info['filename']).strip("/")
                key = bucket.get_key(key_name)
                if key:
                    _mkdir(info['subdir'])
                    key.get_contents_to_filename(info['localpath'])
                    todo.append(info['subdir'])
        reindex_xtf(todo)


def reindex_xtf(todo):
    XTF_HOME='/home/ec2-user/xtf-cpf'
    command = os.path.join(XTF_HOME, 'bin', 'textIndexer')
    if not (todo):
        execute(command)
    else:
        pp(todo)


def execute(command):
    # http://stackoverflow.com/a/4417735/1763984
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        print(line) # yield line


def get_info(bucket, localdir, string):
    """"""
    #      99166-w600735z.xml
    # ark:/99166/w600735z
    #
    def parse_ark(string):
        """match ARKs or filename and parse NAAN from the rest"""
        matchObj = re.match(r'.*(\d\d\d\d\d)(?:-|/)([a-z0-9]*)', string)
        if matchObj:
            naan = matchObj.group(1)
            part = matchObj.group(2)
            return (naan, part)
    try:
        naan, part = parse_ark(string)
    except TypeError:
        return
    subdir, localpath = parse_to_fullpath(naan, part, localdir)
    filename = '{0}-{1}.xml'.format(naan, part)
    return {
        "filename": filename,
        "subdir": subdir,
        "localpath": localpath
    }


def pull_all(bucket, bucketurl, localdir):
    """grab all the files from the bucket"""
    parts = urlparse.urlsplit(bucketurl)
    for key in bucket.list():
        if key.name.startswith(parts.path[1:]):
            info = get_info(bucketurl, localdir, key.name)
            _mkdir(info['subdir'])
            key.get_contents_to_filename(info['localpath'])


def parse_to_fullpath(naan, part, BASE2):
    """ compute local subdir and full path to XML"""
    ark_name = '-'.join([naan, part])
    subdir = os.path.join(BASE2,
                          ark_name[-2:],
                          ark_name)
    fullpath = os.path.join(BASE2,
                            subdir,
                            '{0}.xml'.format(ark_name))
    return subdir, fullpath


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
