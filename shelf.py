## -*- coding: utf-8 -*-
from vendor.Qt import QtCore, QtGui, QtWidgets
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import button_setting
import button
import partition
reload(button)
reload(button_setting)
reload(partition)
import json
import os
import pymel.core as pm
import re
import sys
import copy

class SiShelfWeight(MayaQWidgetDockableMixin, QtWidgets.QTabWidget):
    TITLE = "SiShelf"
    URL = "https://github.com/mochio326/SiShelf"
    PEN_WIDTH = 1  # 矩形の枠の太さ
    CURRENT_TAB_FLAG = '(current)'

    def __init__(self, parent=None):
        super(SiShelfWeight, self).__init__(parent)
        #メモリ管理的おまじない
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        # オブジェクト名とタイトルの変更
        self.setObjectName(self.TITLE)
        self.setWindowTitle(self.TITLE)
        self.setMovable(True)
        self.setAcceptDrops(True)

        self.load_tab_data()

        self.origin = None
        self.band = None
        self.selected = []
        self._floating_save = False
        self.clipboard = None
        self.context_pos = QtCore.QPoint()
        self.cut_flag = False

        self._set_stylesheet()

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.currentChanged.connect(self._current_tab_change)
        self.tabBar().tabMoved.connect(self._tab_moved)

        partition.PartitionWidget(self.currentWidget())

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
        _menu = QtWidgets.QMenu()
        # 項目名と実行する関数の設定
        _menu.addAction('Add Tab', self._add_tab)
        _menu.addAction('Rename Tab', self._rename_tab)
        _menu.addAction('Delete Tab', self._delete_tab)
        _menu.addSeparator()
        _menu.addAction('Add button', self._add_button)
        _menu.addAction('Button default setting', self._button_default_setting)
        _menu.addSeparator()
        _menu.addAction('Edit', self._edit_selected_button)
        _menu.addAction('Delete', self._delete_selected_button)
        _menu.addAction('Copy', self._copy)
        _menu.addAction('Paste', self._paste)
        _menu.addAction('Cut', self._cut)

        curor = QtGui.QCursor.pos()

        _ui = get_show_repr()
        pos = QtCore.QPoint(curor.x() - _ui['x'], curor.y() - _ui['y'])
        # タブバーの高さを考慮
        self.context_pos = QtCore.QPoint(pos.x(), pos.y() - self.sizeHint().height())
        # ボタンが矩形で選択されていなければマウス位置の下のボタンを選択しておく
        if len(self.selected) == 0:
            rect = QtCore.QRect(pos, self.context_pos)
            self._get_button_in_rectangle(rect)
            self._set_stylesheet()
            self.update()
        # マウス位置に出現
        _menu.exec_(curor)

    def _copy(self):
        self.clipboard = copy.deepcopy(self.selected[0].data)

    def _paste(self):
        if self.clipboard is None:
            return
        data = copy.deepcopy(self.clipboard)
        data.position = self.context_pos
        btn = button.create_button(self.currentWidget(), data)
        self.selected = []
        self.repaint()
        self.save_tab_data()
        # カットの場合は貼り付けは一度だけ
        if self.cut_flag is True:
            self.clipboard = None
            self.cut_flag = False

    def _cut(self):
        self._copy()
        self.delete_button(self.selected[0])
        self.cut_flag = True

    def _button_default_setting(self):
        data = self._get_button_default_data()
        data, _result = button_setting.SettingDialog.get_data(self, data)
        if _result is not True:
            print("Cancel.")
            return None
        meke_save_dir()
        path = get_button_default_filepath()
        not_escape_json_dump(path, vars(data))

    def _delete_tab(self):
        _status = QtWidgets.QMessageBox.question(
            self, 'Confirmation',
            'Are you sure you want to delete the tab?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if _status == QtWidgets.QMessageBox.Yes:
            self.removeTab(self.currentIndex())
            self.save_tab_data()
        else:
            return

    def _rename_tab(self):
        new_tab_name, _status = QtWidgets.QInputDialog.getText(
            self,
            'Rename Tab',
            'Specify new tab name',
            QtWidgets.QLineEdit.Normal,
            self.tabText(self.currentIndex())
        )
        if not _status:
            return
        self.setTabText(self.currentIndex(), new_tab_name)
        self.save_tab_data()

    def _add_tab(self):
        new_tab_name, _status = QtWidgets.QInputDialog.getText(
            self,
            'Add New Tab',
            'Specify new tab name',
            QtWidgets.QLineEdit.Normal,
            'Tab{0}'.format(self.count() + 1)
        )
        if not _status:
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

    def _add_button(self):
        data = self._get_button_default_data()
        data.position = self.context_pos
        self.create_button(data)
        self.save_tab_data()

    def delete_button(self, button):
        button.setParent(None)
        button.deleteLater()

    def create_button(self, data):
        data, _result = button_setting.SettingDialog.get_data(self, data)
        if _result is not True:
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

        for _vars in data:
            tab_number = self.count()
            self.insertTab(tab_number, QtWidgets.QWidget(), _vars['name'])
            if _vars['current'] is True:
                self.setCurrentIndex(tab_number)
            for _var in _vars['button']:
                # 辞書からインスタンスのプロパティに代入
                data = button.ButtonData()
                {setattr(data, k, v) for k, v in _var.items()}
                button.create_button(self.widget(tab_number), data)

    def save_tab_data(self):
        ls = []
        current = self.currentIndex()
        for i in range(self.count()):
            _tab_data = {}
            _tab_data['name'] = self.tabText(i)
            # カレントタブ
            _tab_data['current'] = (i == current)
            # ボタンのデータ
            _b = []
            for child in self.widget(i).findChildren(button.ButtonWidget):
                _b.append(vars(child.data))
            _tab_data['button'] = _b
            ls.append(_tab_data)

        meke_save_dir()
        path = self.__get_tab_data_path()
        not_escape_json_dump(path, ls)

    # -----------------------
    # Event
    # -----------------------

    def dropEvent(self, event):
        _mimedata = event.mimeData()
        #ドロップ位置からタブの高さを考慮する
        x = event.pos().x()
        y = event.pos().y() - self.sizeHint().height()
        if y < 0:
            y = 0
        _position = QtCore.QPoint(x, y)

        if _mimedata.hasText() is True or _mimedata.hasUrls() is True:
            data = self._get_button_default_data()
            data.position = _position

            if _mimedata.hasText() is True:
                data.code = _mimedata.text()

            if _mimedata.hasUrls() is True:
                #複数ファイルの場合は最後のファイルが有効になる
                for url in _mimedata.urls():
                    _path = re.sub("^/", "", url.path())
                # 外部エディタから投げ込んだ場合もこちらに来るので回避
                if _path != '':
                    data.externalfile = _path
                    data.use_externalfile = True
                    _info = QtCore.QFileInfo(data.externalfile)
                    _suffix = _info.completeSuffix()
                    if _suffix == 'py':
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
            event.source().move(_position)
            event.source().data.position_x = x
            event.source().data.position_y = y
            self.save_tab_data()

            # よくわからん
            event.setDropAction(QtCore.Qt.MoveAction)
            event.accept()

        elif isinstance(event.source(), partition.PartitionWidget):
            # ドラッグ後のマウスの位置にボタンを配置
            event.source().move(_position)
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
        elif isinstance(event.source(), (button.ButtonWidget, partition.PartitionWidget)):
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

    def closeEvent(self, event):
        if self._floating_save is False:
            if self.isFloating() is True:
                dict_ = get_show_repr()
                meke_save_dir()
                f = open(get_shelf_floating_filepath(), 'w')
                json.dump(dict_, f)
                f.close()
        self._floating_save = True

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

    def _get_button_default_data(self):
        path = get_button_default_filepath()
        data = button.ButtonData()
        js = not_escape_json_load(path)
        if js is not None:
            {setattr(data, k, v) for k, v in js.items()}
        return data

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
    dict_ = {}
    dict_['display'] = False
    dict_['dockable'] = True
    dict_['floating'] = True
    dict_['area'] = None
    dict_['x'] = 0
    dict_['y'] = 0
    dict_['width'] = 400
    dict_['height'] = 150

    _ui = get_ui()
    if _ui is None:
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


def get_save_dir():
    _dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(_dir, 'data')


def get_shelf_docking_filepath():
    return os.path.join(get_save_dir(), 'shelf_docking.json')


def get_button_default_filepath():
    return os.path.join(get_save_dir(), 'button_default.json')


def get_shelf_floating_filepath():
    return os.path.join(get_save_dir(), 'shelf_floating.json')


def meke_save_dir():
    dir_ = get_save_dir()
    if os.path.isdir(dir_) is False:
        os.makedirs(dir_)


def quit_app():
    dict = get_show_repr()
    meke_save_dir()
    _f = open(get_shelf_docking_filepath(), 'w')
    json.dump(dict, _f)
    _f.close()


def make_quit_app_job():
    pm.scriptJob(e=("quitApplication", pm.Callback(quit_app)))


def restoration_docking_ui():
    '''
    ドッキングした状態のUIを復元する
    :return:
    '''
    path = get_shelf_docking_filepath()
    if os.path.isfile(path) is False:
        return
    f = open(path, 'r')
    _dict = json.load(f)
    if _dict['display'] is False:
        return
    if _dict['floating'] is False and _dict['area'] is not None:
        window = SiShelfWeight()
        window.show(
            dockable=True,
            area=_dict['area'],
            floating=_dict['floating'],
            width=_dict['width'],
            height=_dict['height']
        )


def get_floating_data():
    path = get_shelf_floating_filepath()
    if os.path.isfile(path) is False:
        return None
    f = open(path, 'r')
    dict_ = json.load(f)
    return dict_


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
    cursor = QtGui.QCursor.pos()
    floating = get_floating_data()
    if floating is None:
        ui.show(dockable=True, x=cursor.x(), y=cursor.y())
    else:
        ui.show(dockable=True, x=cursor.x(), y=cursor.y(), width=floating['width'], height=floating['height'])
    sys.exit()
    app.exec_()


def main():
    # 画面中央に表示
    ui = make_ui()
    _floating = get_floating_data()
    if _floating is None:
        ui.show(dockable=True)
    else:
        # 保存されたデータのウインドウ位置を使うとウインドウのバーが考慮されてないのでズレる
        # ui.show(dockable=True, x=floating['x'], y=floating['y'], width=floating['width'], height=floating['height'])
        ui.show(dockable=True, width=_floating['width'], height=_floating['height'])
    sys.exit()
    app.exec_()


if __name__ == '__main__':
    main()

#-----------------------------------------------------------------------------
# EOF
#-----------------------------------------------------------------------------
