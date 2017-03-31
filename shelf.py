## -*- coding: utf-8 -*-
from vendor.Qt import QtCore, QtGui, QtWidgets
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import button_setting
import button
reload(button)
reload(button_setting)
import json
import os
import pymel.core as pm


class SiShelfWeight(MayaQWidgetDockableMixin, QtWidgets.QTabWidget):
    TITLE = "SiShelf"
    URL = ""
    # 矩形の枠の太さ
    PEN_WIDTH = 1

    def __init__(self, parent=None):
        super(SiShelfWeight, self).__init__(parent)
        #メモリ管理的おまじない
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        # オブジェクト名とタイトルの変更
        self.setObjectName(self.TITLE)
        self.setWindowTitle(self.TITLE)

        self.insertTab(0, QtWidgets.QWidget(), 'Tab1')
        self.setMovable(True)

        self.setAcceptDrops(True)

        self.resize(400, 150)
        self.origin = None
        self.band = None
        self.selected = []

        self._set_stylesheet()

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)

    def _context_menu(self, event):
        menu = QtWidgets.QMenu()
        # 項目名と実行する関数の設定
        menu.addAction('Add Tab', self._add_tab)
        menu.addSeparator()
        menu.addAction('Edit the selected button', self._edit_selected_button)
        menu.addAction('Delete the selected button', self._delete_selected_button)
        # マウス位置に出現
        menu.exec_(QtGui.QCursor.pos())

    def _add_tab(self):

        new_tab_name, status = QtWidgets.QInputDialog.getText(
            self,
            'Add New Tab',
            'Specify new tab name',
            QtWidgets.QLineEdit.Normal,
            'Tab{0}'.format(self.count() + 1)
        )
        if not status:
            return
        self.insertTab(self.count() + 1, QtWidgets.QWidget(), new_tab_name)
        self.setCurrentIndex(self.count() + 1)

    def _delete_selected_button(self):
        for s in self.selected:
            self.delete_button(s)
        self.selected = []

    def _edit_selected_button(self):
        if len(self.selected) != 1:
            print('Only standalone selection is supported.')
            return
        btn = self.selected[0]
        _re = self.create_button(btn.data)
        if _re is None:
            return
        self.delete_button(btn)

    def delete_button(self, button):
        button.deleteLater()

    def create_button(self, data):
        data, result = button_setting.SettingDialog.get_data(self, data)
        if result is not True:
            print("Cancel.")
            return None
        btn = button.create_button(self.currentWidget(), data)
        self.repaint()
        return btn

    # -----------------------
    # Event
    # -----------------------
    def dropEvent(self, event):
        mimedata = event.mimeData()
        position = event.pos()
        #ドロップ位置からタブの高さを考慮する
        x = event.pos().x()
        y = event.pos().y() - self.sizeHint().height()
        if y < 0:
            y = 0
        position = QtCore.QPoint(x, y)

        if mimedata.hasText() is True or mimedata.hasUrls() is True:
            data = button.ButtonData()

            if mimedata.hasText() is True:
                data.code = mimedata.text()
                data.label = 'newButton'
                data.position = position

            btn = self.create_button(data)

        elif isinstance(event.source(), button.ButtonWidget):
            # ドラッグ後のマウスの位置にボタンを配置
            event.source().move(position)
            event.source().data.position_x = x
            event.source().data.position_y = y

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
        elif isinstance(event.source(), button.ButtonWidget):
            event.accept()
        else:
            event.ignore()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.origin = event.pos()
            self.band = QtCore.QRect()

    def mouseMoveEvent(self, event):

        if self.band is not None:
            self.band = QtCore.QRect(self.origin, event.pos())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return

        if not self.origin:
            self.origin = event.pos()
        rect = QtCore.QRect(self.origin, event.pos()).normalized()

        self.selected = []
        for child in self.findChildren(button.ButtonWidget):
            # 矩形内に位置しているかを判定
            if rect.intersects(self._get_button_absolute_geometry(child)) is False:
                continue
            # アクティブなタブ以外の物は選択対象外
            if child.parent != self.currentWidget():
                continue
            self.selected.append(child)

        self._set_stylesheet()
        self.origin = QtCore.QPoint()
        self.band = None
        self.update()

    def paintEvent(self, event):
        if self.band is not None:
            #矩形範囲の描画
            painter = QtGui.QPainter(self)
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
            print s.objectName()
            css += '#' + s.objectName() + '{border-color:#aaaaaa; border-style:solid; border-width:1px;}'
        self.setStyleSheet(css)


# #################################################################################################
# ここから実行関数
# #################################################################################################

def get_ui():
    ui = {w.objectName(): w for w in QtWidgets.QApplication.allWidgets()}
    if SiShelfWeight.TITLE in ui:
        return ui[SiShelfWeight.TITLE]
    return None


def get_show_repr():
    dict = {}
    dict['display'] = False
    dict['dockable'] = True
    dict['floating'] = True
    dict['area'] = None
    dict['x'] = 0
    dict['y'] = 0
    dict['width'] = 400
    dict['height'] = 150

    ui = get_ui()
    if ui is None:
        return dict

    dict['display'] = True
    dict['dockable'] = ui.isDockable()
    dict['floating'] = ui.isFloating()
    dict['area'] = ui.dockArea()
    if dict['dockable'] is True:
        dock_dtrl = ui.parent()
        pos = dock_dtrl.mapToGlobal(QtCore.QPoint(0, 0))
    else:
        pos = ui.pos()
    sz = ui.geometry().size()
    dict['x'] = pos.x()
    dict['y'] = pos.y()
    dict['width'] = sz.width()
    dict['height'] = sz.height()
    return dict


def get_json_path():
    dir = os.path.dirname(os.path.abspath(__file__))
    path = '{0}\\{1}.json'.format(dir, SiShelfWeight.TITLE)
    return path


def quit_app():
    dict = get_show_repr()
    f = open(get_json_path(), 'w')
    json.dump(dict, f)
    f.close()


def make_quit_app_job():
    pm.scriptJob(e=("quitApplication", pm.Callback(quit_app)))


def restoration_ui():
    path = get_json_path()
    if os.path.isfile(path) is False:
        return
    f = open(path, 'r')
    dict = json.load(f)
    if dict['display'] is False:
        return
    print dict
    if dict['floating'] is False and dict['area'] is not None:
        window = SiShelfWeight()
        window.show(
            dockable=True,
            area=dict['area'],
            floating=dict['floating'],
            width=dict['width'],
            height=dict['height']
        )

def main():
    # 同名のウインドウが存在したら削除
    ui = get_ui()
    if ui is not None:
        ui.close()
    app = QtWidgets.QApplication.instance()
    window = SiShelfWeight()
    window.show(dockable=True)
    return ui


if __name__ == '__main__':
    main()

#-----------------------------------------------------------------------------
# EOF
#-----------------------------------------------------------------------------
