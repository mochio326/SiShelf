## -*- coding: utf-8 -*-
from vendor.Qt import QtCore, QtGui, QtWidgets
import random
import string
import os
import json

class PartsData(object):
    def __init__(self):
        self.use_label = True
        self.label = ''
        self.label_font_size = 10
        self.position_x = 0
        self.position_y = 0
        self.width = 100
        self.height = 50


    position = property(doc='position property')
    @position.getter
    def position(self):
        return QtCore.QPoint(self.position_x, self.position_y)
    @position.setter
    def position(self, data):
        self.position_x = data.x()
        self.position_y = data.y()

    size = property(doc='size property')
    @size.getter
    def size(self):
        if self.size_flag is False:
            return None
        return QtCore.QSize(self.width, self.height)


def random_string(length, seq=string.digits + string.ascii_lowercase):
    sr = random.SystemRandom()
    return ''.join([sr.choice(seq) for i in xrange(length)])




# http://qiita.com/tadokoro/items/131268c9a0fd1cf85bf4
# 日本語をエスケープさせずにjsonを読み書きする
def not_escape_json_dump(path, data):
    text = json.dumps(data, sort_keys=True, ensure_ascii=False, indent=2)
    with open(path, 'w') as fh:
        fh.write(text.encode('utf-8'))


def not_escape_json_load(path):
    if os.path.isfile(path) is False:
        return None
    with open(path) as fh:
        data = json.loads(fh.read(), "utf-8")
    return data

#-----------------------------------------------------------------------------
# EOF
#-----------------------------------------------------------------------------
