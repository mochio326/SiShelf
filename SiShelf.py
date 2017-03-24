## -*- coding: utf-8 -*-
from vendor.Qt import QtCore, QtGui, QtWidgets
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin
import ButtonSetting
import ShelfButton
reload(ShelfButton)
reload(ButtonSetting)

class SiShelfWeight(MayaQWidgetBaseMixin, QtWidgets.QDialog):
    TITLE = "SiShelf"
    URL = ""
    # 矩形の枠の太さ
    PEN_WIDTH = 1

    def __init__(self, parent=None):
        super(SiShelfWeight, self).__init__(parent)
        #メモリ管理的おまじない
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        # オブジェクト名とタイトルの変更
        self.setObjectName(self.TITLE)
        self.setWindowTitle(self.TITLE)

        self.setAcceptDrops(True)

        self.resize(400, 150)
        self.btn = []
        self.button = None
        self.origin = None
        self.band = None
        self.selected = []

        self._set_stylesheet()

        #右クリック時のメニュー
        self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        menu_delete = QtWidgets.QAction(self)
        menu_delete.setText("Delete the selected button")
        menu_delete.triggered.connect(self.delete_selected_button)
        self.addAction(menu_delete)

    def delete_selected_button(self):
        for s in self.selected:
            s.deleteLater()
        self.selected = []
    # -----------------------
    # Event
    # -----------------------
    def dropEvent(self, event):
        mimedata = event.mimeData()
        position = event.pos()
        #urllist = mimedata.urls()

        if mimedata.hasText() is True or mimedata.hasUrls() is True:
            btn_data = ShelfButton.ButtonData()

            if mimedata.hasText() is True:
                btn_data.code = mimedata.text()
                btn_data.label = 'newButton' + str(len(self.btn))
                btn_data.position = position

            btn_data, result = ButtonSetting.SettingDialog.get_data(self, btn_data)
            if result is not True:
                print("Cancel.")
                return
            if btn_data.label == '':
                return

            btn = ShelfButton.create_button(self, btn_data, len(self.btn))
            self.repaint()
            self.btn.append(btn)

        elif isinstance(event.source(), ShelfButton.ButtonWidget):
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
        elif isinstance(event.source(), ShelfButton.ButtonWidget):
            event.accept()
        else:
            event.ignore()

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return
        self.origin = event.pos()
        self.band = QtCore.QRect()

    def mouseMoveEvent(self, event):

        if self.band is None:
            return
        self.band = QtCore.QRect(self.origin, event.pos())
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return

        if not self.origin:
            self.origin = event.pos()
        rect = QtCore.QRect(self.origin, event.pos()).normalized()

        self.selected = []
        for child in self.findChildren(ShelfButton.ButtonWidget):
            if rect.intersects(self._get_button_absolute_geometry(child)):
                self.selected.append(child)

        self._set_stylesheet()

        self.origin = QtCore.QPoint()
        self.band = None
        self.update()

    def paintEvent(self, event):
        if self.band is None:
            return

        #event.save()
        painter = QtGui.QPainter(self)
        #painter.setRenderHint(QtGui.QPainter.Antialiasing, True)  # アンチエイリアス
        color = QtGui.QColor(255, 255, 255, 125)
        pen = QtGui.QPen(color, self.PEN_WIDTH)
        painter.setPen(pen)
        painter.drawRect(self.band)
        painter.restore()

    # -----------------------
    # Others
    # -----------------------
    def _get_button_absolute_geometry(self, button):
        '''
        type:ShelfButton.ButtonWidget -> QtCore.QSize
        '''
        geo = button.geometry()
        point = button.mapTo(self, geo.topLeft())
        point -= geo.topLeft()
        geo = QtCore.QRect(point, geo.size())
        return geo

    def _set_stylesheet(self):
        css = 'QToolButton:hover{background:#707070;}'
        # 選択中のボタンを誇張
        for s in self.selected:
            css += '#button_' + str(s.number) + '{border-color:#aaaaaa; border-style:solid; border-width:1px;}'
        self.setStyleSheet(css)

        

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
