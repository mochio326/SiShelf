## -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
import random
import string
import os
import json
import maya.cmds as cmds
import re

TITLE = "SiShelf"

class PartsData(object):
    def __init__(self):
        self.use_label = True
        self.label = 'label'
        self._label_font_size = 10
        self.position_x = 0
        self.position_y = 0
        self.width = 100
        self.height = 50

        self.position_offset_x = 0
        self.position_offset_y = 0
        self.scale = 1

    label_font_size = property(doc='label_font_size property')
    @label_font_size.getter
    def label_font_size(self):
        return self._label_font_size * self.scale

    @label_font_size.setter
    def label_font_size(self, size):
        self._label_font_size = size

    position = property(doc='position property')
    @position.getter
    def position(self):
        _x = (self.position_x + self.position_offset_x) * self.scale
        _y = (self.position_y + self.position_offset_y) * self.scale
        return QtCore.QPoint(_x , _y)

    @position.setter
    def position(self, data):
        self.position_x = data.x()
        self.position_y = data.y()

    size = property(doc='size property')
    @size.getter
    def size(self):
        if self.size_flag is False:
            return None
        return QtCore.QSize(self.width * self.scale, self.height * self.scale)


def button_css(buttons, css):
    if isinstance(buttons, list) is False:
        buttons = [buttons]
    css += 'QToolButton:hover{background:#707070;}'
    # Maya2016からはボタンのsetColorでは背景色が変わらなくなっていたのでスタイルシートに全て設定
    for _b in buttons:
        css += '#' + _b.objectName() + '{'
        if _b.data.use_label_color is True:
            css += 'color:' + _b.data.label_color + ';'
        if _b.data.use_bgcolor is True:
            css += 'background:' + _b.data.bgcolor + ';'
        css += 'border-color:#606060; border-style:solid; border-width:1px;}'

        css += ':hover#' + _b.objectName() + '{background:#707070;}'
        # 押した感を出す
        css += ':pressed#' + _b.objectName() + '{padding:1px -1px -1px 1px;}'
    return css


def get_ui(name, weight_type):
    all_ui = {w.objectName(): w for w in QtWidgets.QApplication.allWidgets()}
    ui = []
    for k, v in all_ui.items():
        if name not in k:
            continue
        # 2017だとインスタンスの型をチェックしないと別の物まで入ってきてしまうらしい
        # 2016以前だと比較すると通らなくなる…orz
        if maya_version() >= 2017:
            if v.__class__.__name__ == weight_type:
                return v
        else:
            return v
    return None


# -----------------------
# データ保存・読込関連
# -----------------------
def load_floating_data():
    path = get_shelf_floating_filepath()
    if os.path.isfile(path) is False:
        return None
    f = open(path, 'r')
    dict_ = json.load(f)
    return dict_


def floating_save(ui):
    if ui.isFloating() is True:
        dict_ = {}
        dict_['width'] = ui.width()
        dict_['height'] = ui.height()
        make_save_dir()
        f = open(get_shelf_floating_filepath(), 'w')
        json.dump(dict_, f)
        f.close()


def get_show_repr(vis_judgment=True):
    '''
    UIの状態を取得
    :param vis_judgment:表示状態を考慮するか
    :return:
    '''
    dict_ = {}
    dict_['display'] = False
    dict_['dockable'] = True
    dict_['floating'] = True
    dict_['area'] = None
    dict_['x'] = 0
    dict_['y'] = 0
    dict_['width'] = 400
    dict_['height'] = 150

    _ui = get_ui(TITLE, 'SiShelfWeight')
    if _ui is None:
        return dict_

    if vis_judgment is True and _ui.isVisible() is False:
        return dict_

    dict_['display'] = True
    dict_['dockable'] = _ui.isDockable()
    dict_['floating'] = _ui.isFloating()
    dict_['area'] = _ui.dockArea()
    if dict_['dockable'] is True:
        dock_dtrl = _ui.parent()
        _pos = dock_dtrl.mapToGlobal(QtCore.QPoint(0, 0))
    else:
        _pos = _ui.pos()
    _sz = _ui.geometry().size()
    dict_['x'] = _pos.x()
    dict_['y'] = _pos.y()
    dict_['width'] = _sz.width()
    dict_['height'] = _sz.height()
    return dict_


# -----------------------
# path関連
# -----------------------
def get_save_dir():
    _dir = os.environ.get('MAYA_APP_DIR')
    return os.path.join(_dir, 'SiShelf_data')


def get_shelf_docking_filepath():
    return os.path.join(get_save_dir(), 'shelf_docking.json')


def get_button_default_filepath():
    return os.path.join(get_save_dir(), 'button_default.json')


def get_partition_default_filepath():
    return os.path.join(get_save_dir(), 'partition_default.json')


def get_shelf_floating_filepath():
    return os.path.join(get_save_dir(), 'shelf_floating.json')
    

def get_shelf_option_filepath():
    return os.path.join(get_save_dir(), 'shelf_option.json')


def get_tab_data_path():
    make_save_dir()
    path = os.path.join(get_save_dir(), 'parts.json')
    return path


def make_save_dir():
    dir_ = get_save_dir()
    if os.path.isdir(dir_) is False:
        os.makedirs(dir_)


# -----------------------
# その他
# -----------------------
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


def random_string(length, seq=string.digits + string.ascii_lowercase):
    sr = random.SystemRandom()
    return ''.join([sr.choice(seq) for i in xrange(length)])


def maya_api_version():
    return int(cmds.about(api=True))

def maya_version():
    return int(cmds.about(v=True)[:4])


def escape(s, quoted='\'"\\', escape='\\'):
    return re.sub(
            '[%s]' % re.escape(quoted),
            lambda mo: escape + mo.group(),
            s)


def script_execute(code, source_type):
    '''
    maya内でスクリプトを実行する
    :param code: string
    :param source_type: 'mel' or 'python'
    :return:
    '''
    window = cmds.window()
    cmds.columnLayout()
    cmds.cmdScrollFieldExecuter(t=code, opc=1, sln=1, exa=1, sourceType=source_type)
    cmds.deleteUI(window)


# 実行関数を文字列から動的生成用文字列
_CONTEXT_FUNC = """
def _f():
    if {0} is True:
        code = readfile(r'{1}')
    else:
        code = '''{2}'''
    source_type = '{3}'
    lib.script_execute(code, source_type)
"""

#-----------------------------------------------------------------------------
# EOF
#-----------------------------------------------------------------------------
