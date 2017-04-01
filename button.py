## -*- coding: utf-8 -*-
from vendor.Qt import QtCore, QtGui, QtWidgets
import random
import string
import maya.cmds as cmds
import os


class ButtonWidget(QtWidgets.QToolButton):

    def __init__(self, parent, data, preview=False):
        self.parent = parent
        super(ButtonWidget, self).__init__(parent)
        self.data = data
        self.preview = preview
        print vars(data)

    def mouseMoveEvent(self, event):
        # 中クリックだけドラッグ＆ドロップ可能にする
        if event.buttons() != QtCore.Qt.MidButton:
            return

        # ドラッグ＆ドロップされるデータ形式を代入
        mimedata = QtCore.QMimeData()

        drag = QtGui.QDrag(self)
        drag.setMimeData(mimedata)
        # ドロップした位置にボタンの左上をセット
        drag.setHotSpot(event.pos() - self.rect().topLeft())
        drop_action = drag.exec_(QtCore.Qt.MoveAction)

    def mousePressEvent(self, event):
        # ボタンが押されたときのボタンの色の変化
        QtWidgets.QPushButton.mousePressEvent(self, event)

        # 左クリック
        if self.preview is True:
            return
        if event.button() == QtCore.Qt.LeftButton:
            print('mousePressEvent : ' + self.data.label)
            if self.data.use_externalfile is True:
                code = readfile(self.data.externalfile)
            else:
                code = self.data.code
            source_type = self.data.script_language.lower()
            script_execute(code, source_type)


class ButtonData(object):
    def __init__(self, label='', code='', path=''):
        self.label = label
        self.label_font_size = 10
        self.tooltip = ''
        self.bool_tooltip = True
        self.code = code
        self.script_language = 'Python'
        self.position_x = 0
        self.position_y = 0
        self.fix_size_flag = False
        self.btn_size_x = 100
        self.btn_size_y = 50
        self.icon_file = ':/polySphere.png'

        self.use_label = True
        self.use_icon = False
        self.icon_style = 0

        self.icon_size_x = 30
        self.icon_size_y = 30

        self.bgcolor = '#4a4a4a'
        self.use_bgcolor = False

        if path != '':
            self.use_externalfile = True
        else:
            self.use_externalfile = False
        self.externalfile = path

    position = property(doc='position property')
    @position.getter
    def position(self):
        return QtCore.QPoint(self.position_x, self.position_y)
    @position.setter
    def position(self, data):
        self.position_x = data.x()
        self.position_y = data.y()

    icon = property(doc='icon property')
    @icon.getter
    def icon(self):
        # QIconは元サイズより大きくできない？
        # http://blogs.yahoo.co.jp/hmfjm910/3060875.html
        image = QtGui.QImage(self.icon_file)
        pixmap = QtGui.QPixmap.fromImage(image)
        pixmap.scaled(150, 150, QtCore.Qt.KeepAspectRatio, QtCore.Qt.FastTransformation)
        return QtGui.QIcon(pixmap)

    fix_size = property(doc='fix_size property')
    @fix_size.getter
    def fix_size(self):
        if self.fix_size_flag is False:
            return None
        return QtCore.QSize(self.btn_size_x, self.btn_size_y)

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


def random_string(length, seq=string.digits + string.ascii_lowercase):
    sr = random.SystemRandom()
    return ''.join([sr.choice(seq) for i in xrange(length)])


def create_button(parent, data, preview=False):
    btn = ButtonWidget(parent, data, preview)
    btn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    btn.setObjectName(random_string(15))
    btn.setIcon(data.icon)
    btn.setIconSize(data.icon_size)
    if data.fix_size is not None:
        btn.setFixedSize(data.fix_size)
    btn.setText(data.label)
    font = btn.font()
    font.setPointSize(data.label_font_size)
    btn.setFont(font)
    btn.setToolButtonStyle(data.style)
    if data.bool_tooltip is True:
        if data.use_externalfile is True:
            btn.setToolTip(data.externalfile)
        else:
            btn.setToolTip(data.code)
    else:
        btn.setToolTip(data.tooltip)

    if data.use_bgcolor is True:
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(data.bgcolor))
        btn.setPalette(palette)

    btn.show()
    btn.move(data.position)
    return btn


def readfile(path):
    if os.path.exists(path) is False:
        return ''
    f = open(path, "r")
    t = f.read()
    f.close()
    return t


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

#-----------------------------------------------------------------------------
# EOF
#-----------------------------------------------------------------------------
