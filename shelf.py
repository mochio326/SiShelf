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
import re
import sys

class SiShelfWeight(MayaQWidgetDockableMixin, QtWidgets.QTabWidget):
    TITLE = "SiShelf"
    URL = "https://github.com/mochio326/SiShelf"
    # 矩形の枠の太さ
    PEN_WIDTH = 1
    CURRENT_TAB_FLAG = '(current)'

    def __init__(self, parent=None):
        super(SiShelfWeight, self).__init__(parent)
        #メモリ管理的おまじない
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        # オブジェクト名とタイトルの変更
        self.setObjectName(self.TITLE)
        self.setWindowTitle(self.TITLE)

        self.load_tab_data()
        self.setMovable(True)

        self.setAcceptDrops(True)

        self.resize(400, 150)
        self.origin = None
        self.band = None
        self.selected = []

        self._set_stylesheet()

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.currentChanged.connect(self._current_tab_change)

        self.tabBar().tabMoved.connect(self._tab_moved)

    def _current_tab_change(self):
        self.selected = []
        self._set_stylesheet()
        self.update()
        self.save_tab_data()

    def _tab_moved(self, event):
        self.save_tab_data()

    # -----------------------
    # ContextMenu
    # -----------------------
    def _context_menu(self, event):
        menu = QtWidgets.QMenu()
        # 項目名と実行する関数の設定
        menu.addAction('Add Tab', self._add_tab)
        menu.addAction('Rename Tab', self._rename_tab)
        menu.addSeparator()
        menu.addAction('New button', self._new_button)
        menu.addAction('Edit selected button', self._edit_selected_button)
        menu.addAction('Delete selected button', self._delete_selected_button)
        menu.addAction('Button default setting', self._button_default_setting)

        curor = QtGui.QCursor.pos()
        # ボタンが矩形で選択されていなければマウス位置の下のボタンを選択しておく
        if len(self.selected) == 0:
            _ui = get_show_repr()
            _pos = QtCore.QPoint(curor.x() - _ui['x'], curor.y() - _ui['y'])
            rect = QtCore.QRect(_pos, _pos)
            self._get_button_in_rectangle(rect)
            self._set_stylesheet()
            self.update()
        # マウス位置に出現
        menu.exec_(curor)

    def _button_default_setting(self):
        pass

    def _rename_tab(self):
        new_tab_name, status = QtWidgets.QInputDialog.getText(
            self,
            'Rename Tab',
            'Specify new tab name',
            QtWidgets.QLineEdit.Normal,
            self.tabText(self.currentIndex())
        )
        if not status:
            return
        self.setTabText(self.currentIndex(), new_tab_name)
        self.save_tab_data()


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
        self.save_tab_data()

    def _delete_selected_button(self):
        for s in self.selected:
            self.delete_button(s)
        self.selected = []
        self.save_tab_data()

    def _edit_selected_button(self):
        if len(self.selected) != 1:
            print('Only standalone selection is supported.')
            return
        btn = self.selected[0]
        _re = self.create_button(btn.data)
        if _re is None:
            return
        self.delete_button(btn)
        self.save_tab_data()

    def _new_button(self):
        data = button.ButtonData()
        self.create_button(data)
        self.save_tab_data()

    def delete_button(self, button):
        button.deleteLater()

    def create_button(self, data):
        data, result = button_setting.SettingDialog.get_data(self, data)
        if result is not True:
            print("Cancel.")
            return None
        btn = button.create_button(self.currentWidget(), data)
        self.selected = []
        self.repaint()
        return btn

    # -----------------------
    # Save Load
    # -----------------------
    def __get_tab_data_path(self):
        meke_save_dir()
        path = os.path.join(get_save_dir(), 'parts.json')
        return path

    def load_tab_data(self):
        path = self.__get_tab_data_path()
        data = not_escape_json_load(path)
        if data is None:
            self.insertTab(0, QtWidgets.QWidget(), 'Tab1')
            return

        for vars in data:
            tab_number = self.count()
            self.insertTab(tab_number, QtWidgets.QWidget(), vars['name'])
            if vars['current'] is True:
                self.setCurrentIndex(tab_number)
            for var in vars['button']:
                # 辞書からインスタンスのプロパティに代入
                data = button.ButtonData()
                {setattr(data, k, v) for k, v in var.items()}
                button.create_button(self.widget(tab_number), data)

    def save_tab_data(self):
        ls = []
        current = self.currentIndex()
        for i in range(self.count()):
            tab_data = {}
            tab_data['name'] = self.tabText(i)
            # カレントタブ
            tab_data['current'] = (i == current)
            # ボタンのデータ
            b = []
            for child in self.widget(i).findChildren(button.ButtonWidget):
                b.append(vars(child.data))
            tab_data['button'] = b
            ls.append(tab_data)

        meke_save_dir()
        path = self.__get_tab_data_path()
        not_escape_json_dump(path, ls)

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
            data.position = position

            if mimedata.hasText() is True:
                data.code = mimedata.text()

            if mimedata.hasUrls() is True:
                #複数ファイルの場合は最後のファイルが有効になる
                for url in mimedata.urls():
                    path = re.sub("^/", "", url.path())
                # 外部エディタから投げ込んだ場合もこちらに来るので回避
                if path != '':
                    data.externalfile = path
                    data.use_externalfile = True
                    _info = QtCore.QFileInfo(data.externalfile)
                    _suffix = _info.completeSuffix()
                    if _suffix == "py":
                        data.script_language = 'Python'
                    elif _suffix == 'mel':
                        data.script_language = 'MEL'
                    else:
                        print('This file format is not supported.')
                        return
                    data.label = _info.completeBaseName()

            self.create_button(data)
            self.save_tab_data()

        elif isinstance(event.source(), button.ButtonWidget):
            # ドラッグ後のマウスの位置にボタンを配置
            event.source().move(position)
            event.source().data.position_x = x
            event.source().data.position_y = y
            self.save_tab_data()

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
        self._get_button_in_rectangle(rect)
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
    def _get_button_in_rectangle(self, rect):
        self.selected = []
        for child in self.findChildren(button.ButtonWidget):
            # アクティブなタブ以外の物は選択対象外
            if child.parent != self.currentWidget():
                continue
            # 矩形内に位置しているかを判定
            if rect.intersects(self._get_button_absolute_geometry(child)) is False:
                continue
            self.selected.append(child)

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
            css += '#' + s.objectName() + '{border-color:#aaaaaa; border-style:solid; border-width:1px;}'
        self.setStyleSheet(css)


# #################################################################################################

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


def get_save_dir():
    dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(dir, 'data')


def get_shelf_data_path():
    return os.path.join(get_save_dir(), 'shelf.json')

def meke_save_dir():
    dir = get_save_dir()
    if os.path.isdir(dir) is False:
        os.makedirs(dir)


def quit_app():
    dict = get_show_repr()
    meke_save_dir()
    f = open(get_shelf_data_path(), 'w')
    json.dump(dict, f)
    f.close()

    ui = get_ui()
    if ui is not None:
        ui.save_tab_data()


def make_quit_app_job():
    pm.scriptJob(e=("quitApplication", pm.Callback(quit_app)))


def restoration_ui():
    path = get_shelf_data_path()
    if os.path.isfile(path) is False:
        return
    f = open(path, 'r')
    dict = json.load(f)
    if dict['display'] is False:
        return
    if dict['floating'] is False and dict['area'] is not None:
        window = SiShelfWeight()
        window.show(
            dockable=True,
            area=dict['area'],
            floating=dict['floating'],
            width=dict['width'],
            height=dict['height']
        )


def make_ui():
    # 同名のウインドウが存在したら削除
    ui = get_ui()
    if ui is not None:
        ui.close()
    app = QtWidgets.QApplication.instance()
    ui = SiShelfWeight()
    return ui


def popup():
    # マウス位置にポップアップ
    ui = make_ui()
    curor = QtGui.QCursor.pos()
    ui.show(dockable=True, x=curor.x(), y=curor.y())
    sys.exit()
    app.exec_()


def main():
    # 画面中央に表示
    ui = make_ui()
    ui.show(dockable=True)
    sys.exit()
    app.exec_()


if __name__ == '__main__':
    main()

#-----------------------------------------------------------------------------
# EOF
#-----------------------------------------------------------------------------
