## -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
try:
    from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
except:
    # 2014以下のバージョン用
    MayaQWidgetDockableMixin = object
from . import button_setting
from . import button
from . import partition
from . import partition_setting
from . import lib
from . import shelf_option

import json
import os
import pymel.core as pm
import maya.cmds as cmds
import re
import sys
import copy

class SiShelfWeight(MayaQWidgetDockableMixin, QtWidgets.QTabWidget):
    TITLE = "SiShelf"
    URL = "https://github.com/mochio326/SiShelf"
    PEN_WIDTH = 1  # 矩形の枠の太さ

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
        self.parts_moving = False
        self.shelf_option = shelf_option.OptionData()

        self.set_stylesheet()

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.currentChanged.connect(self._current_tab_change)
        self.tabBar().tabMoved.connect(self._tab_moved)

    def _current_tab_change(self):
        self.selected = []
        self.set_stylesheet()
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
        _menu.addAction('Add button', self._add_button)
        _menu.addAction('Add partition', self._add_partition)
        _menu.addSeparator()
        _menu.addAction('Edit', self._edit)
        _menu.addAction('Delete', self._delete)
        _menu.addAction('Copy', self._copy)
        _menu.addAction('Paste', self._paste)
        _menu.addAction('Cut', self._cut)
        _menu.addSeparator()

        _tb = _menu.addMenu('Tab')
        _tb.addAction('Add', self._add_tab)
        _tb.addAction('Rename', self._rename_tab)
        _tb.addAction('Delete', self._delete_tab)

        _df = _menu.addMenu('Default setting')
        _df.addAction('Button', self._button_default_setting)
        _df.addAction('Partition', self._partition_default_setting)

        _menu.addSeparator()
        _menu.addAction('Option', self._option)

        self._select_cursor_pos_parts()
        # マウス位置に出現
        cursor = QtGui.QCursor.pos()
        _menu.exec_(cursor)

    def _option(self):
        self.shelf_option = shelf_option.OptionDialog.open(self)

    def _copy(self):
        self.clipboard = copy.deepcopy(self.selected[0].data)

    def _paste(self):
        if self.clipboard is None:
            return
        data = copy.deepcopy(self.clipboard)
        data.position = self.context_pos

        if isinstance(data, button.ButtonData):
            button.create(self.currentWidget(), data)
        elif isinstance(data, partition.PartitionData):
            partition.create(self.currentWidget(), data)

        self.selected = []
        self.repaint()
        self.save_tab_data()
        # カットの場合は貼り付けは一度だけ
        if self.cut_flag is True:
            self.clipboard = None
            self.cut_flag = False

    def _cut(self):
        self._copy()
        self.delete_parts(self.selected[0])
        self.cut_flag = True

    def _button_default_setting(self):
        data = self._get_button_default_data()
        data, _result = button_setting.SettingDialog.get_data(self, data)
        if _result is not True:
            print("Cancel.")
            return None
        lib.make_save_dir()
        path = lib.get_button_default_filepath()
        lib.not_escape_json_dump(path, vars(data))

    def _partition_default_setting(self):
        data = self._get_partition_default_data()
        data, _result = partition_setting.SettingDialog.get_data(self, data)
        if _result is not True:
            print("Cancel.")
            return None
        lib.make_save_dir()
        path = lib.get_partition_default_filepath()
        lib.not_escape_json_dump(path, vars(data))

    def _delete_tab(self):
        if self.count() == 1:
            return
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

    def _delete(self):
        for s in self.selected:
            self.delete_parts(s)
        self.selected = []
        self.save_tab_data()

    def _edit(self):
        if len(self.selected) != 1:
            print('Only standalone selection is supported.')
            return
        parts = self.selected[0]

        if isinstance(parts.data, button.ButtonData):
            _re = self.create_button(parts.data)
        elif isinstance(parts.data, partition.PartitionData):
            _re = self.create_partition(parts.data)

        if _re is None:
            return
        self.delete_parts(parts)
        self.set_stylesheet()
        self.save_tab_data()

    def _add_button(self):
        data = self._get_button_default_data()
        data.position = self.context_pos
        self.create_button(data)
        self.save_tab_data()

    def _add_partition(self):
        data = self._get_partition_default_data()
        data.position = self.context_pos
        self.create_partition(data)
        self.save_tab_data()

    def delete_parts(self, widget):
        widget.setParent(None)
        widget.deleteLater()

    def create_button(self, data):
        return self._create_parts(button_setting, button, data)

    def create_partition(self, data):
        return self._create_parts(partition_setting, partition, data)

    def _create_parts(self, ui_obj, data_obj, data):
        data, _result = ui_obj.SettingDialog.get_data(self, data)
        if _result is not True:
            print("Cancel.")
            return None
        parts = data_obj.create(self.currentWidget(), data)
        self.selected = []
        self.repaint()
        return data

    # -----------------------
    # Save Load
    # -----------------------
    def __get_tab_data_path(self):
        lib.make_save_dir()
        path = os.path.join(lib.get_save_dir(), 'parts.json')
        return path

    def load_tab_data(self):
        path = self.__get_tab_data_path()
        data = lib.not_escape_json_load(path)
        if data is None:
            self.insertTab(0, QtWidgets.QWidget(), 'Tab1')
            return

        for _vars in data:
            tab_number = self.count()
            self.insertTab(tab_number, QtWidgets.QWidget(), _vars['name'])
            if _vars['current'] is True:
                self.setCurrentIndex(tab_number)

            if _vars.get('button') is not None:
                for _var in _vars['button']:
                    # 辞書からインスタンスのプロパティに代入
                    data = button.ButtonData()
                    for k, v in _var.items():
                        setattr(data, k, v)
                    button.create(self.widget(tab_number), data)

            if _vars.get('partition') is not None:
                for _var in _vars['partition']:
                    # 辞書からインスタンスのプロパティに代入
                    data = partition.PartitionData()
                    for k, v in _var.items():
                        setattr(data, k, v)
                    partition.create(self.widget(tab_number), data)

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

            # 仕切り線のデータ
            _p = []
            for child in self.widget(i).findChildren(partition.PartitionWidget):
                _p.append(vars(child.data))
            _tab_data['partition'] = _p

            ls.append(_tab_data)

        lib.make_save_dir()
        path = self.__get_tab_data_path()
        lib.not_escape_json_dump(path, ls)

    # -----------------------
    # Event
    # -----------------------

    def dropEvent(self, event):
        _mimedata = event.mimeData()

        if _mimedata.hasText() is True or _mimedata.hasUrls() is True:
            # ドロップ位置をボタンの左上にする
            # ドロップ位置からタブの高さを考慮する
            x = event.pos().x()
            y = event.pos().y() - self.sizeHint().height()
            if y < 0:
                y = 0
            _position = QtCore.QPoint(x, y)

            data = self._get_button_default_data()
            data.position = _position

            if _mimedata.hasText() is True:
                data.code = _mimedata.text()

            if _mimedata.hasUrls() is True:
                #複数ファイルの場合は最後のファイルが有効になる
                for url in _mimedata.urls():  # PySide
                    if hasattr(url, 'path'):
                        _path = re.sub("^/", "", url.path())
                    else:  # PySide2
                        _path = re.sub("^file:///", "", url.url())
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
                    data.code = ''

            self.create_button(data)
            self.save_tab_data()

        elif isinstance(event.source(), (button.ButtonWidget, partition.PartitionWidget)):

            if len(self.selected) > 1:
                # 複数選択されていたらまとめて移動を優先
                self._selected_parts_move(event.pos())
            else:
                self._parts_move(event.source(), event.pos())
                self.save_tab_data()
                self.origin = QtCore.QPoint()

            # よくわからん
            event.setDropAction(QtCore.Qt.MoveAction)
            event.accept()

        self.parts_moving = False
        self.repaint()

    def dragMoveEvent(self, event):
        # パーツを移動中の描画更新
        if len(self.selected) > 0:
            self.parts_moving = True
            self._selected_parts_move(event.pos(), False, False)
        self.repaint()

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
        self.origin = event.pos()
        if event.button() == QtCore.Qt.LeftButton:
            self.band = QtCore.QRect()
            self.parts_moving = False

        if event.button() == QtCore.Qt.MiddleButton:
            self._select_cursor_pos_parts()
            if len(self.selected) <= 1:
                self.set_stylesheet()
        self.repaint()

    def mouseMoveEvent(self, event):
        if self.band is not None:
            self.band = QtCore.QRect(self.origin, event.pos())
        else:
            # パーツを移動中の描画更新
            if len(self.selected) > 0:
                self.parts_moving = True
                self._selected_parts_move(event.pos(), False, False)

        self.repaint()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if not self.origin:
                self.origin = event.pos()
            rect = QtCore.QRect(self.origin, event.pos()).normalized()
            self._get_parts_in_rectangle(rect)
            self.set_stylesheet()
            self.origin = QtCore.QPoint()
            self.band = None

        # 選択中のパーツを移動
        if event.button() == QtCore.Qt.MiddleButton:
            self._selected_parts_move(event.pos())

        self.parts_moving = False
        self.repaint()

    def paintEvent(self, event):
        if self.band is not None:
            #矩形範囲の描画
            painter = QtGui.QPainter(self)
            color = QtGui.QColor(255, 255, 255, 125)
            pen = QtGui.QPen(color, self.PEN_WIDTH)
            painter.setPen(pen)
            painter.drawRect(self.band)
            painter.restore()

        if self.parts_moving is True \
                and self.shelf_option.snap_active is True\
                and self.shelf_option.snap_grid is True:
            self.draw_snap_gide()

    def draw_snap_gide(self):
        # スナップガイドの表示
        painter = QtGui.QPainter(self)
        color = QtGui.QColor(255, 255, 255, 40)
        pen = QtGui.QPen(color, self.PEN_WIDTH)
        pen.setStyle(QtCore.Qt.DashDotLine)
        painter.setPen(pen)

        snap_unit_x = self.shelf_option.snap_width
        snap_unit_y = self.shelf_option.snap_height
        _tab_h = self.sizeHint().height() - 4

        # 横線
        for i in range(self.height() / snap_unit_y):
            _h = snap_unit_y * i + _tab_h
            line = QtCore.QLine(QtCore.QPoint(0, _h), QtCore.QPoint(self.width(), _h))
            painter.drawLine(line)
        # 縦線
        for i in range(self.width() / snap_unit_x + 1):
            _w = snap_unit_x * i + 1
            line = QtCore.QLine(QtCore.QPoint(_w, _tab_h), QtCore.QPoint(_w, self.height() + _tab_h))
            painter.drawLine(line)
        painter.restore()

    def closeEvent(self, event):
        # 2017以前だとhideEventにすると正常にウインドウサイズなどの情報が取ってこれない
        if lib.maya_api_version() < 201700:
            self.floating_save()
        super(SiShelfWeight, self).closeEvent(event)

    def hideEvent(self, event):
        # 2017だとcloseEventにするとイベントが動かない…
        if lib.maya_api_version() >= 201700:
            self.floating_save()

    def floating_save(self):
        if self._floating_save is False:
            if self.isFloating() is True:
                #dict_ = get_show_repr(False)
                dict_ = {}
                _sz = self.frameGeometry().size()

                # 2017だと取得してきたサイズ情報が-4pxになってる。。なぜかは分からない…
                # SP3では修正されていた
                '''
                add = 0
                if lib.maya_api_version() >= 201700:
                    add = 4
                '''
                dict_['width'] = self.width()
                dict_['height'] = self.height()

                lib.make_save_dir()
                f = open(lib.get_shelf_floating_filepath(), 'w')
                json.dump(dict_, f)
                f.close()
        self._floating_save = True

    # -----------------------
    # Others
    # -----------------------
    def _selected_parts_move(self, after_pos, save=True, data_pos_update=True):
        # 選択中のパーツを移動
        if len(self.selected) > 0:
            for p in self.selected:
                self._parts_move(p, after_pos, data_pos_update)
            if save is True:
                self.origin = QtCore.QPoint()
                self.save_tab_data()

    def _parts_move(self, parts, after_pos, data_pos_update=True):
        # ドラッグ中に移動した相対位置を加算
        _rect = QtCore.QRect(self.origin, after_pos)
        _x = parts.data.position_x + _rect.width()
        _y = parts.data.position_y + _rect.height()
        if _x < 0:
            _x = 0
        if _y < 0:
            _y = 0

        if self.shelf_option.snap_active is True:
            _x = int(_x / self.shelf_option.snap_width) * self.shelf_option.snap_width
            _y = int(_y / self.shelf_option.snap_height) * self.shelf_option.snap_height

        _position = QtCore.QPoint(_x, _y)
        parts.move(_position)
        if data_pos_update is True:
            parts.data.position_x = _x
            parts.data.position_y = _y

    def _get_parts_in_rectangle(self, rect):
        self.selected = []
        chidren = []
        chidren.extend(self.currentWidget().findChildren(button.ButtonWidget))
        chidren.extend(self.currentWidget().findChildren(partition.PartitionWidget))

        for child in chidren:
            # 矩形内に位置しているかを判定
            if rect.intersects(self._get_parts_absolute_geometry(child)) is False:
                continue
            self.selected.append(child)

    def _get_parts_absolute_geometry(self, parts):
        '''
        type:ShelfButton.ButtonWidget -> QtCore.QSize
        '''
        geo = parts.geometry()
        point = parts.mapTo(self, geo.topLeft())
        point -= geo.topLeft()
        geo = QtCore.QRect(point, geo.size())
        return geo

    def set_stylesheet(self):
        css = ''
        buttons = self.currentWidget().findChildren(button.ButtonWidget)
        css = lib.button_css(buttons, css)

        # 選択中のパーツを誇張
        for s in self.selected:
            css += '#' + s.objectName() + '{'
            if isinstance(s.data, button.ButtonData):
                if s.data.use_bgcolor is True:
                    css += 'background:' + s.data.bgcolor + ';'
            css += 'border-color:red; border-style:solid; border-width:1px;}'
        self.setStyleSheet(css)

    def _get_button_default_data(self):
        path = lib.get_button_default_filepath()
        data = button.ButtonData()
        js = lib.not_escape_json_load(path)
        if js is not None:
            for k, v in js.items():
                setattr(data, k, v)
        return data

    def _get_partition_default_data(self):
        path = lib.get_partition_default_filepath()
        data = partition.PartitionData()
        js = lib.not_escape_json_load(path)
        if js is not None:
            {setattr(data, k, v) for k, v in js.items()}
        return data

    def _select_cursor_pos_parts(self):
        '''
        複数選択されていなければマウス直下のパーツを選択する
        :return:
        '''
        cursor = QtGui.QCursor.pos()
        _ui = get_show_repr()
        pos = QtCore.QPoint(cursor.x() - _ui['x'], cursor.y() - _ui['y'])
        # タブバーの高さを考慮 （ただ実際のタブの大きさと数ピクセルずれてる気がする
        self.context_pos = QtCore.QPoint(pos.x(), pos.y() - self.sizeHint().height())
        # パーツが矩形で選択されていなければマウス位置の下のボタンを選択しておく
        # 1個選択状態の場合は選択し直した方が直感的な気がする
        if len(self.selected) <= 1:
            _l = len(self.selected)
            _s = self.selected

            rect = QtCore.QRect(pos, pos)
            # ドッキングしてる状態だとタブの高さを考慮したほうがいい！？なんじゃこの挙動は…
            if self.isFloating() is False and self.dockArea() is not None:
                rect = QtCore.QRect(self.context_pos, self.context_pos)
            self._get_parts_in_rectangle(rect)
            if len(self.selected) > 1:
                self.selected = [self.selected[0]]
            if _l == 1 and len(self.selected) == 0:
                self.selected = _s
            self.set_stylesheet()
            self.repaint()

# #################################################################################################


def get_ui():
    all_ui = {w.objectName(): w for w in QtWidgets.QApplication.allWidgets()}
    ui = []
    for k, v in all_ui.items():
        if SiShelfWeight.TITLE not in k:
            continue
        # 2017だとインスタンスの型をチェックしないと別の物まで入ってきてしまうらしい
        # 2016以前だと比較すると通らなくなる…orz
        if lib.maya_api_version() >= 201700:
            if v.__class__.__name__ == 'SiShelfWeight':
                return v
        else:
            return v
    return None


def get_show_repr(vis_judgment=True):
    '''

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

    _ui = get_ui()
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


def quit_app():
    dict = get_show_repr()
    lib.make_save_dir()
    _f = open(lib.get_shelf_docking_filepath(), 'w')
    json.dump(dict, _f)
    _f.close()


def make_quit_app_job():
    pm.scriptJob(e=("quitApplication", pm.Callback(quit_app)))


def restoration_docking_ui():
    '''
    ドッキングした状態のUIを復元する
    :return:
    '''
    path = lib.get_shelf_docking_filepath()
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
        workspaceControlName = window.objectName() + 'WorkspaceControl'
        #cmds.workspaceControl(workspaceControlName, e=True, ttc=["AttributeEditor", -1], wp="preferred", mw=420)
        #cmds.workspaceControl(workspaceControlName, e=True, dtm=[_dict['area'], -1], wp="preferred", mw=420)


def get_floating_data():
    path = lib.get_shelf_floating_filepath()
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

    # 2017からはWorkspaceControlが採用されて、専用コマンドで消さないといけなくなった？？
    # https://gist.github.com/liorbenhorin/217bfb7e54c6f75b9b1b2b3d73a1a43a
    if lib.maya_api_version() >= 201700:
        control = SiShelfWeight.TITLE + 'WorkspaceControl'
        if cmds.workspaceControl(control, q=True, exists=True):
            cmds.workspaceControl(control, e=True, close=True)
            cmds.deleteUI(control, control=True)

        if cmds.workspaceControlState(control, ex=True):
            cmds.workspaceControlState(control, r=True)

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
    try:
        if _floating is None:
            ui.show(dockable=True)

        else:
            # 保存されたデータのウインドウ位置を使うとウインドウのバーが考慮されてないのでズレる
            # ui.show(dockable=True, x=floating['x'], y=floating['y'], width=floating['width'], height=floating['height'])
            ui.show(dockable=True, width=_floating['width'], height=_floating['height'])


    except TypeError:
        # バージョン判定して分岐したほうが良い
        ui.show()
    sys.exit()
    app.exec_()


if __name__ == '__main__':
    main()

#-----------------------------------------------------------------------------
# EOF
#-----------------------------------------------------------------------------
