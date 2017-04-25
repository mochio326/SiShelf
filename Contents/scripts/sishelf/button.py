## -*- coding: utf-8 -*-
import os
import maya.cmds as cmds

from .vendor.Qt import QtCore, QtGui, QtWidgets
from . import lib


class ButtonWidget(QtWidgets.QToolButton):

    def __init__(self, parent, data, preview=False):
        self.parent = parent
        super(ButtonWidget, self).__init__(parent)
        self.data = data
        self.preview = preview

    def mouseMoveEvent(self, event):
        # 中クリックだけドラッグ＆ドロップ可能にする
        if event.buttons() != QtCore.Qt.MidButton:
            return
        # ドラッグ＆ドロップされるデータ形式を代入
        mimedata = QtCore.QMimeData()
        drag = QtGui.QDrag(self)
        drag.setMimeData(mimedata)
        drag.exec_(QtCore.Qt.MoveAction)

    def mousePressEvent(self, event):
        QtWidgets.QToolButton.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        # 左クリック
        if self.preview is True:
            return

        if event.button() == QtCore.Qt.LeftButton:
            # ボタン以外のところでマウスを離したらキャンセル扱い
            if event.pos().x() < 0 \
                    or event.pos().x() > self.width() \
                    or event.pos().y() < 0 \
                    or event.pos().y() > self.height():
                print('Cancel : ' + self.data.label)
                return

            event.pos().x(), event.pos().y()

            if self.data.type_ == 0:
                print('Run : ' + self.data.label)
                if self.data.use_externalfile is True:
                    code = readfile(self.data.externalfile)
                else:
                    code = self.data.code
                source_type = self.data.script_language.lower()
                lib.script_execute(code, source_type)
            else:
                self._context_menu()
        QtWidgets.QToolButton.mouseReleaseEvent(self, event)

    def _context_menu(self):
        _menu = QtWidgets.QMenu()
        # 項目名と実行する関数の設定
        menu_data_context(_menu, self.data.menu_data)
        cursor = QtGui.QCursor.pos()
        _menu.exec_(cursor)


class ButtonData(lib.PartsData):
    def __init__(self, label='newButton', code='', path=''):
        super(ButtonData, self).__init__()
        self.label = label

        self.tooltip = ''
        self.bool_tooltip = True
        self.code = code
        self.script_language = 'Python'
        self.type_ = 0  # 0:def 1:MenuButton
        self.size_flag = False
        self.icon_file = ':/polySphere.png'

        self.use_icon = False
        self.icon_style = 0

        self.icon_size_x = 30
        self.icon_size_y = 30

        self.bgcolor = '#4a4a4a'
        self.use_bgcolor = False

        self.label_color = '#eeeeee'
        self.use_label_color = False

        self.menu_data = []

        if path != '':
            self.use_externalfile = True
        else:
            self.use_externalfile = False
        self.externalfile = path

    icon = property(doc='icon property')
    @icon.getter
    def icon(self):
        # QIconは元サイズより大きくできない？
        # http://blogs.yahoo.co.jp/hmfjm910/3060875.html
        image = QtGui.QImage(self.icon_file)
        pixmap = QtGui.QPixmap.fromImage(image)
        pixmap.scaled(150, 150, QtCore.Qt.KeepAspectRatio, QtCore.Qt.FastTransformation)
        return QtGui.QIcon(pixmap)

    icon_size = property(doc='icon_size property')
    @icon_size.getter
    def icon_size(self):
        return QtCore.QSize(self.icon_size_x, self.icon_size_y)

    style = property(doc='style property')
    @style.getter
    def style(self):
        if self.use_label is True and self.use_icon is False:
            # テキストのみ
            return QtCore.Qt.ToolButtonTextOnly
        elif self.use_label is False and self.use_icon is True:
            # アイコンのみ
            return QtCore.Qt.ToolButtonIconOnly
        elif self.use_label is True and self.use_icon is True:
            if self.icon_style == 0:
                # アイコンの横にテキスト
                return QtCore.Qt.ToolButtonTextBesideIcon
            else:
                # アイコンの下にテキスト
                return QtCore.Qt.ToolButtonTextUnderIcon
        else:
            # 例外はとりあえずテキストのみ
            return QtCore.Qt.ToolButtonTextOnly


def create(parent, data, preview=False):
    widget = ButtonWidget(parent, data, preview)
    widget.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    widget.setObjectName(lib.random_string(15))
    widget.setIcon(data.icon)
    widget.setIconSize(data.icon_size)
    if data.size is not None:
        widget.setFixedSize(data.size)
    widget.setText(data.label)
    font = widget.font()
    font.setPointSize(data.label_font_size)
    widget.setFont(font)
    widget.setToolButtonStyle(data.style)
    if data.bool_tooltip is True:
        if data.use_externalfile is True:
            widget.setToolTip(data.externalfile)
        else:
            widget.setToolTip(data.code)
    else:
        widget.setToolTip(data.tooltip)

    if data.use_bgcolor is True:
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(data.bgcolor))
        widget.setPalette(palette)

    widget.show()
    widget.move(data.position)
    return widget


def readfile(path):
    if os.path.exists(path) is False:
        return ''
    f = open(path, "r")
    t = f.read()
    f.close()
    return t


def get_default():
    path = lib.get_button_default_filepath()
    data = ButtonData()
    js = lib.not_escape_json_load(path)
    if js is not None:
        for k, v in js.items():
            setattr(data, k, v)
    return data


def make_menu_button_dict():
    return {'label':' test001',
    'use_externalfile':False,
    'externalfile':'',
    'code':'',
    'script_language':'Python'
    }


def menu_data_context(menu, data):
    for i in range(len(data)):
        _d = data[i]

        if _d['label'].count('----') >= 1:
            menu.addSeparator()
            continue

        # codeは文字をエスケープしておかないとエラーになるので注意
        exec (lib._CONTEXT_FUNC.format(
            _d['use_externalfile'],
            _d['externalfile'],
            lib.escape(_d['code'].encode('cp932')),
            _d['script_language'].lower()
        ))
        menu.addAction(_d['label'], _f)


def normal_data_context(menu, data):
        # codeは文字をエスケープしておかないとエラーになるので注意
        exec (lib._CONTEXT_FUNC.format(
            data.use_externalfile,
            data.externalfile,
            lib.escape(data.code.encode('cp932')),
            data.script_language.lower()
        ))

        _act = menu.addAction(data.label, _f)
        if data.use_icon:
            _act.setIcon(data.icon)
        '''
        if data.bool_tooltip is True:
            if data.use_externalfile is True:
                _act.setToolTip(data.externalfile)
            else:
                _act.setToolTip(data.code)
        else:
            _act.setToolTip(data.tooltip)
        '''
#-----------------------------------------------------------------------------
# EOF
#-----------------------------------------------------------------------------
