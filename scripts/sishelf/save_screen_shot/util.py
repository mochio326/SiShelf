import os
import sys
import time


def CheckDirectory(filePath):
    dir_name = os.path.dirname(filePath)

    if not os.path.isdir(dir_name):
        os.makedirs(dir_name)


def GetTempImgPath(extension="bmp"):
    tmp_dir = ""
    if sys.platform == "win32":
        tmp_dir = os.environ["TEMP"]
    elif sys.platform == "darwin":
        tmp_dir = os.environ["TMPDIR"]
    else:
        tmp_dir = "/var/tmp"

    if not os.path.isdir(tmp_dir):
        os.makedirs(tmp_dir)

    return os.path.join(tmp_dir, "%s_%d.%s" % (__package__, int(time.time()), extension))
