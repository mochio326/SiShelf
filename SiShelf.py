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
