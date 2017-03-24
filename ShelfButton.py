## -*- coding: utf-8 -*-
from vendor.Qt import QtCore, QtGui, QtWidgets

class ButtonWidget(QtWidgets.QToolButton):

    def __init__(self, parent, btn_data, number=-1):
        super(ButtonWidget, self).__init__(parent)
        self.btn_data = btn_data
        self.number = number

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

        # 左クリックしたときにコンソールにpress表示
        if event.button() == QtCore.Qt.LeftButton:
            print('mousePressEvent : ' + self.btn_data.label)
            exec(self.btn_data.code)


class ButtonData(object):
    def __init__(self, label='', code=''):
        self.label = label
        self.code = code
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

def create_button(parent, btn_data, number):
    btn = ButtonWidget(parent, btn_data, number)
    btn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    btn.setObjectName('button_'+str(btn.number))
    btn.setIcon(btn_data.icon)
    btn.setIconSize(btn_data.icon_size)
    if btn_data.fix_size is not None:
        btn.setFixedSize(btn_data.fix_size)
    btn.setText(btn_data.label)
    btn.setToolButtonStyle(btn_data.style)

    btn.show()
    btn.move(btn_data.position)
    return btn

#-----------------------------------------------------------------------------
# EOF
#-----------------------------------------------------------------------------
