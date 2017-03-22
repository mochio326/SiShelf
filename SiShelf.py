## -*- coding: utf-8 -*-
from vendor.Qt import QtCore, QtGui, QtWidgets
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin
import ButtonSetting

class ShelfButton(QtWidgets.QPushButton):

    def __init__(self, title, parent, code, number):
        super(ShelfButton, self).__init__(title, parent)
        self.title = title
        self.number = number
        self.code = code

    def mouseMoveEvent(self, e):
        # 中クリックだけドラッグ＆ドロップ可能にする
        if e.buttons() != QtCore.Qt.MidButton:
            return

        # ドラッグ＆ドロップされるデータ形式を代入
        mimedata = QtCore.QMimeData()

        drag = QtGui.QDrag(self)
        drag.setMimeData(mimedata)
        # ドロップした位置にボタンの左上をセット
        drag.setHotSpot(e.pos() - self.rect().topLeft())
        drop_action = drag.exec_(QtCore.Qt.MoveAction)


    def mousePressEvent(self, e):
        # ボタンが押されたときのボタンの色の変化
        QtWidgets.QPushButton.mousePressEvent(self, e)

        # 左クリックしたときにコンソールにpress表示
        if e.button() == QtCore.Qt.LeftButton:
            print('mousePressEvent : ' + self.title)
            exec(self.code)


class SiShelfWeight(MayaQWidgetBaseMixin, QtWidgets.QDialog):
    TITLE = "SiShelf"
    URL = ""

    def __init__(self, parent=None):
        super(SiShelfWeight, self).__init__(parent)
        #メモリ管理的おまじない
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        # オブジェクト名とタイトルの変更
        self.setObjectName(self.TITLE)
        self.setWindowTitle(self.TITLE)

        # Widget配置
        #self.layout = QtWidgets.QGridLayout()
        #self.layout.setSpacing(0)
        #self.layout.setDirection(QtCore.Qt.RightToLeft)

        self.setAcceptDrops(True)

        #self.setLayout(self.layout)

        self.resize(400, 150)
        self.btn = []
        self.button = None

    # -----------------------
    # Event
    # -----------------------
    def dropEvent(self, event):
        mimedata = event.mimeData()
        position = event.pos()
        #urllist = mimedata.urls()

        if mimedata.hasText() is True or mimedata.hasUrls() is True:
            title, result = ButtonSetting.SettingDialog.get_canvas_size(self)
            if result is not True:
                print("Cancel.")
                return
            if title == '':
                return

            btn = ShelfButton(title, self, mimedata.text(), len(self.btn))
            btn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            btn.setObjectName(mimedata.text())
            btn.show()
            btn.move(position)
            #self.layout.addWidget(btn)
            self.repaint()
            self.btn.append(btn)

        elif isinstance(event.source(), ShelfButton):
            # ドラッグ後のマウスの位置にボタンを配置
            self.btn[event.source().number].move(position)

            # よくわからん
            event.setDropAction(QtCore.Qt.MoveAction)
            event.accept()

    def dragEnterEvent(self, event):
        '''
        ドラッグされたオブジェクトを許可するかどうかを決める
        ドラッグされたオブジェクトが、テキストかファイルなら許可する
        '''

        mime = event.mimeData()
        if mime.hasText() is True or mime.hasUrls() is True:
            event.accept()
        elif isinstance(event.source(), ShelfButton):
            event.accept()
        else:
            event.ignore()
    # -----------------------
    # Others
    # -----------------------


# #################################################################################################
# ここから実行関数
# #################################################################################################

def main():
    # 同名のウインドウが存在したら削除
    ui = {w.objectName(): w for w in QtWidgets.QApplication.topLevelWidgets()}
    if SiShelfWeight.TITLE in ui:
        ui[SiShelfWeight.TITLE].close()

    app = QtWidgets.QApplication.instance()
    window = SiShelfWeight()
    window.show()
    #return ui


if __name__ == '__main__':
    main()

#-----------------------------------------------------------------------------
# EOF
#-----------------------------------------------------------------------------
