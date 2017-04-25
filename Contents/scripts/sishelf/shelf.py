## -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
from . import button_setting
from . import button
from . import partition
from . import partition_setting
from . import lib
from . import shelf_option

import json
import os
import os.path
import pymel.core as pm
import re
import copy

if lib.maya_api_version() < 201500:
    # 2014以下のバージョン用
    MayaQWidgetDockableMixin = object

elif lib.maya_api_version() < 201700:
    from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

elif 201700 <= lib.maya_api_version() and lib.maya_api_version() < 201800:
    # TODO: 新バージョンが出たら確認すること
    from .patch import m2017
    MayaQWidgetDockableMixin = m2017.MayaQWidgetDockableMixin2017

else:
    from maya.app.general.mayaMixin import MayaQWidgetDockableMixin


class SiShelfWeight(MayaQWidgetDockableMixin, QtWidgets.QTabWidget):
    URL = "https://github.com/mochio326/SiShelf"
    VAR = '1.6.0'
    PEN_WIDTH = 1  # 矩形の枠の太さ

    def __init__(self, parent=None, load_file=None, edit_lock=False):
        super(SiShelfWeight, self).__init__(parent)
        #メモリ管理的おまじない
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        # オブジェクト名とタイトルの変更
        self.setObjectName(lib.TITLE)
        self.setWindowTitle(lib.TITLE)

        self.load_file = load_file
        self.edit_lock = edit_lock

        if self.edit_lock is False:
            self.setMovable(True)
            self.setAcceptDrops(True)

        self.load_all_tab_data()

        self._origin = None
        self._band = None
        self._selected = []
        self._floating_save = False
        self._clipboard = None
        self._context_pos = QtCore.QPoint()
        self._cut_flag = False
        self._parts_moving = False
        self._shelf_option = shelf_option.OptionData()

        self._set_stylesheet()

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.currentChanged.connect(self._current_tab_change)
        self.tabBar().tabMoved.connect(self._tab_moved)

    def _current_tab_change(self):
        self._selected = []
        self._set_stylesheet()
        self.update()
        self.save_all_tab_data()

    def _tab_moved(self, event):
        self.save_all_tab_data()

    # -----------------------
    # ContextMenu
    # -----------------------
    def _context_menu(self, event):
        _menu = QtWidgets.QMenu()
        # 項目名と実行する関数の設定
        if self.edit_lock is False:
            print self.currentWidget().reference
            if self.currentWidget().reference is None:
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
            if self.currentWidget().reference is None:
                _tb.addAction('Export', self._export_tab)
                _tb.addAction('Import', self._import_tab)
                _tb.addAction('External reference', self._reference_tab)  # 外部参照設定
            else:
                _tb.addAction('Remove external reference', self._remove_reference_tab)  # 外部参照設定解除

            _df = _menu.addMenu('Default setting')
            _df.addAction('Button', self._button_default_setting)
            _df.addAction('Partition', self._partition_default_setting)

            _menu.addSeparator()
            _menu.addAction('Option', self._option)
        _menu.addAction('Version information', self._info)

        self._select_cursor_pos_parts()
        # マウス位置に出現
        cursor = QtGui.QCursor.pos()
        _menu.exec_(cursor)

    def _info(self):
        _status = QtWidgets.QMessageBox.information(
            self, 'Version information',
            'SiShelf ' + self.VAR,
            QtWidgets.QMessageBox.Ok,
            QtWidgets.QMessageBox.Ok
        )

    def _option(self):
        self._shelf_option = shelf_option.OptionDialog.open(self)
        self._set_stylesheet()

    def _copy(self):
        self._clipboard = copy.deepcopy(self._selected[0].data)

    def _paste(self):
        if self._clipboard is None:
            return
        data = copy.deepcopy(self._clipboard)
        data.position = self._context_pos

        if isinstance(data, button.ButtonData):
            button.create(self.currentWidget(), data)
        elif isinstance(data, partition.PartitionData):
            partition.create(self.currentWidget(), data)

        self._selected = []
        self.repaint()
        self.save_all_tab_data()
        # カットの場合は貼り付けは一度だけ
        if self._cut_flag is True:
            self._clipboard = None
            self._cut_flag = False

    def _cut(self):
        self._copy()
        self.delete_parts(self._selected[0])
        self._cut_flag = True

    def _button_default_setting(self):
        data = button.get_default()
        data, _result = button_setting.SettingDialog.get_data(self, data)
        if _result is not True:
            print("Cancel.")
            return None
        lib.make_save_dir()
        path = lib.get_button_default_filepath()
        lib.not_escape_json_dump(path, vars(data))

    def _partition_default_setting(self):
        data = partition.get_default()
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
            self.save_all_tab_data()
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
        self.save_all_tab_data()

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
        self.insertTab(self.count() + 1, ShelfTabWeight(), new_tab_name)
        self.setCurrentIndex(self.count() + 1)
        self.save_all_tab_data()

    def _export_tab(self):
        file_name = QtWidgets.QFileDialog.getSaveFileName(
            self,
            'Export Tab',
            os.environ.get('MAYA_APP_DIR'),
            'Json Files (*.json)'
        )
        if not file_name:
            return
        root, ext = os.path.splitext(file_name[0])
        if ext != '.json':
            return
        _data = self.currentWidget().get_all_parts_dict()
        lib.not_escape_json_dump(file_name[0], _data)

    def _import_tab(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Import Tab',
            os.environ.get('MAYA_APP_DIR'),
            'Json Files (*.json)'
        )
        if not file_name:
            return
        root, ext = os.path.splitext(file_name[0])
        if ext != '.json':
            return
        _status = QtWidgets.QMessageBox.question(
            self, 'Confirmation',
            'Existing parts of the tab will be deleted. Are you sure to execute?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if _status == QtWidgets.QMessageBox.Yes:
            _data = lib.not_escape_json_load(file_name[0])
            self.currentWidget().all_delete_parts()
            self.currentWidget().create_parts(_data)
            self._set_stylesheet()
            self.save_all_tab_data()

    def _reference_tab(self):
        _p = os.environ.get('MAYA_APP_DIR')
        if self.currentWidget().reference is not None:
            _p = self.currentWidget().reference
        else:
            # 外部参照を初めて設定する場合
            _status = QtWidgets.QMessageBox.question(
                self, 'Confirmation',
                'Existing parts of the tab will be deleted. Are you sure to execute?',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            if _status == QtWidgets.QMessageBox.No:
                return

        file_name = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Reference Tab',
            _p,
            'Json Files (*.json)'
        )
        if not file_name:
            return
        root, ext = os.path.splitext(file_name[0])
        if ext != '.json':
            return

        icon = QtGui.QIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowDown))
        self.setTabIcon(self.currentIndex(), icon)

        self.currentWidget().reference = file_name[0]
        _data = lib.not_escape_json_load(file_name[0])
        self.currentWidget().all_delete_parts()
        self.currentWidget().create_parts(_data)
        self._set_stylesheet()
        self.save_all_tab_data()

    def _remove_reference_tab(self):
        if self.currentWidget().reference is not None:
            self.currentWidget().reference = None
            self.currentWidget().all_delete_parts()
            self._set_stylesheet()
            self.save_all_tab_data()
            self.setTabIcon(self.currentIndex(), QtGui.QIcon())


    def _delete(self):
        for s in self._selected:
            self.delete_parts(s)
        self._selected = []
        self.save_all_tab_data()

    def _edit(self):
        if len(self._selected) != 1:
            print('Only standalone selection is supported.')
            return
        parts = self._selected[0]

        if isinstance(parts.data, button.ButtonData):
            _re = self.create_button(parts.data)
        elif isinstance(parts.data, partition.PartitionData):
            _re = self.create_partition(parts.data)

        if _re is None:
            return
        self.delete_parts(parts)
        self._set_stylesheet()
        self.save_all_tab_data()

    def _add_button(self):
        data = button.get_default()
        data.position = self._context_pos
        self.create_button(data)
        self.save_all_tab_data()
        self._set_stylesheet()

    def _add_partition(self):
        data = partition.get_default()
        data.position = self._context_pos
        self.create_partition(data)
        self.save_all_tab_data()

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
        data_obj.create(self.currentWidget(), data)
        self._selected = []
        self.repaint()
        return data

    # -----------------------
    # Save Load
    # -----------------------
    def load_all_tab_data(self):
        if self.load_file is None:
            path = lib.get_tab_data_path()
        else:
            path = self.load_file
        data = lib.not_escape_json_load(path)
        if data is None:
            self.insertTab(0, ShelfTabWeight(), 'Tab1')
            return

        for _vars in data:
            tab_number = self.count()
            self.insertTab(tab_number, ShelfTabWeight(), _vars['name'])

            if _vars['current'] is True:
                self.setCurrentIndex(tab_number)
            if _vars.get('reference') is None:
                self.widget(tab_number).create_parts(_vars)
            else:
                if _vars['reference'] is None:
                    self.widget(tab_number).create_parts(_vars)
                else:
                    icon = QtGui.QIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowDown))
                    self.setTabIcon(tab_number, icon)
                    _data = lib.not_escape_json_load(_vars['reference'])
                    self.widget(tab_number).reference = _vars['reference']
                    self.widget(tab_number).all_delete_parts()
                    self.widget(tab_number).create_parts(_data)

    def save_all_tab_data(self):
        if self.edit_lock is True:
            return

        ls = []
        current = self.currentIndex()
        for i in range(self.count()):
            _tab_data = {}
            _tab_data['name'] = self.tabText(i)
            _tab_data['current'] = (i == current)  # カレントタブ
            if self.widget(i).reference is None:
                _tab_data.update(self.widget(i).get_all_parts_dict())
            _tab_data['reference'] = self.widget(i).reference
            ls.append(_tab_data)

        lib.make_save_dir()
        if self.load_file is None:
            path = lib.get_tab_data_path()
        else:
            path = self.load_file
        lib.not_escape_json_dump(path, ls)

    # -----------------------
    # Event
    # -----------------------

    def dropEvent(self, event):
        if self.edit_lock is True or self.currentWidget().reference is not None:
            return

        _mimedata = event.mimeData()

        if _mimedata.hasText() is True or _mimedata.hasUrls() is True:
            # ドロップ位置をボタンの左上にする
            # ドロップ位置からタブの高さを考慮する
            x = event.pos().x()
            y = event.pos().y() - self.sizeHint().height()
            if y < 0:
                y = 0
            _position = QtCore.QPoint(x, y)

            data = button.get_default()
            data.position = _position

            if _mimedata.hasText() is True:
                data.code = _mimedata.text()

            if _mimedata.hasUrls() is True:
                #複数ファイルの場合は最後のファイルが有効になる
                for url in _mimedata.urls():
                    if hasattr(url, 'path'):  # PySide
                        _path = re.sub("^/", "", url.path())
                    else:  # PySide2
                        _path = re.sub("^file:///", "", url.url())
                # 外部エディタから投げ込んだ場合もこちらに来るので回避
                if _path != '':
                    data.externalfile = _path
                    data.use_externalfile = True
                    _info = QtCore.QFileInfo(_path)
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
            self.save_all_tab_data()

        elif isinstance(event.source(), (button.ButtonWidget, partition.PartitionWidget)):

            if len(self._selected) > 1:
                # 複数選択されていたらまとめて移動を優先
                self._selected_parts_move(event.pos())
            else:
                self._parts_move(event.source(), event.pos())
                self.save_all_tab_data()
                self._origin = QtCore.QPoint()

            # よくわからん
            event.setDropAction(QtCore.Qt.MoveAction)
            event.accept()

        self._parts_moving = False
        self.repaint()

    def dragMoveEvent(self, event):
        if self.edit_lock is True or self.currentWidget().reference is not None:
            return
        # パーツを移動中の描画更新
        if len(self._selected) > 0:
            self._parts_moving = True
            self._selected_parts_move(event.pos(), False, False)
        self.repaint()

    def dragEnterEvent(self, event):
        '''
        ドラッグされたオブジェクトを許可するかどうかを決める
        ドラッグされたオブジェクトが、テキストかファイルなら許可する
        '''
        if self.edit_lock is True or self.currentWidget().reference is not None:
            return
        mime = event.mimeData()
        if mime.hasText() is True or mime.hasUrls() is True:
            event.accept()
        elif isinstance(event.source(), (button.ButtonWidget, partition.PartitionWidget)):
            event.accept()
        else:
            event.ignore()

    def mousePressEvent(self, event):
        if self.edit_lock is True or self.currentWidget().reference is not None:
            return

        self._origin = event.pos()
        if event.button() == QtCore.Qt.LeftButton:
            self._band = QtCore.QRect()
            self._parts_moving = False

        if event.button() == QtCore.Qt.MiddleButton:
            self._select_cursor_pos_parts()
            if len(self._selected) <= 1:
                self._set_stylesheet()
        self.repaint()

    def mouseMoveEvent(self, event):
        if self.edit_lock is True or self.currentWidget().reference is not None:
            return

        if self._band is not None:
            self._band = QtCore.QRect(self._origin, event.pos())
        else:
            # パーツを移動中の描画更新
            if len(self._selected) > 0:
                self._parts_moving = True
                self._selected_parts_move(event.pos(), False, False)

        self.repaint()

    def mouseReleaseEvent(self, event):
        if self.edit_lock is True or self.currentWidget().reference is not None:
            return

        if event.button() == QtCore.Qt.LeftButton:
            if not self._origin:
                self._origin = event.pos()
            rect = QtCore.QRect(self._origin, event.pos()).normalized()
            self._get_parts_in_rectangle(rect)
            self._set_stylesheet()
            self._origin = QtCore.QPoint()
            self._band = None

        # 選択中のパーツを移動
        if event.button() == QtCore.Qt.MiddleButton:
            self._selected_parts_move(event.pos())

        self._parts_moving = False
        self.repaint()

    def paintEvent(self, event):
        # 矩形範囲の描画
        if self._band is not None:
            painter = QtGui.QPainter(self)
            color = QtGui.QColor(255, 255, 255, 125)
            pen = QtGui.QPen(color, self.PEN_WIDTH)
            painter.setPen(pen)
            painter.drawRect(self._band)
            painter.restore()
        # ガイドグリッドの描画
        if self._parts_moving is True \
                and self._shelf_option.snap_active is True\
                and self._shelf_option.snap_grid is True:
            self._draw_snap_gide()

    def closeEvent(self, event):
        if self.edit_lock is False:
            # 2017以前だとhideEventにすると正常にウインドウサイズなどの情報が取ってこれない
            if lib.maya_api_version() < 201700:
                if self._floating_save is False:
                    lib.floating_save(self)
                self._floating_save = True
        # superだと2017でエラーになったため使用中止
        # super(SiShelfWeight, self).closeEvent(event)
        QtWidgets.QWidget.close(self)

    # -----------------------
    # Others
    # -----------------------
    def _selected_parts_move(self, after_pos, save=True, data_pos_update=True):
        # 選択中のパーツを移動
        if len(self._selected) > 0:
            for p in self._selected:
                self._parts_move(p, after_pos, data_pos_update)
            if save is True:
                self._origin = QtCore.QPoint()
                self.save_all_tab_data()

    def _parts_move(self, parts, after_pos, data_pos_update=True):
        # ドラッグ中に移動した相対位置を加算
        _rect = QtCore.QRect(self._origin, after_pos)
        _x = parts.data.position_x + _rect.width()
        _y = parts.data.position_y + _rect.height()
        if _x < 0:
            _x = 0
        if _y < 0:
            _y = 0

        if self._shelf_option.snap_active is True:
            _x = int(_x / self._shelf_option.snap_width) * self._shelf_option.snap_width
            _y = int(_y / self._shelf_option.snap_height) * self._shelf_option.snap_height

        _position = QtCore.QPoint(_x, _y)
        parts.move(_position)
        if data_pos_update is True:
            parts.data.position_x = _x
            parts.data.position_y = _y

    def _get_parts_in_rectangle(self, rect):
        self._selected = []
        chidren = []
        chidren.extend(self.currentWidget().findChildren(button.ButtonWidget))
        chidren.extend(self.currentWidget().findChildren(partition.PartitionWidget))

        for child in chidren:
            # 矩形内に位置しているかを判定
            if rect.intersects(self._get_parts_absolute_geometry(child)) is False:
                continue
            self._selected.append(child)

    def _get_parts_absolute_geometry(self, parts):
        '''
        type:ShelfButton.ButtonWidget -> QtCore.QSize
        '''
        geo = parts.geometry()
        point = parts.mapTo(self, geo.topLeft())
        point -= geo.topLeft()
        geo = QtCore.QRect(point, geo.size())
        return geo

    def _set_stylesheet(self):
        css = ''

        # タブ
        css += 'QTabBar::tab { ' \
                'height: ' + str(self._shelf_option.tab_height) + 'px;' \
                'font-size: ' + str(self._shelf_option.tab_label_size) + 'pt;' \
                '}'

        # ボタン
        buttons = self.currentWidget().findChildren(button.ButtonWidget)
        css = lib.button_css(buttons, css)

        # 選択中のパーツを誇張
        if self.edit_lock is False  or self.currentWidget().reference is None:
            for s in self._selected:
                css += '#' + s.objectName() + '{'
                if isinstance(s.data, button.ButtonData):
                    if s.data.use_bgcolor is True:
                        css += 'background:' + s.data.bgcolor + ';'
                css += 'border-color:red; border-style:solid; border-width:1px;}'
        self.setStyleSheet(css)

    def _select_cursor_pos_parts(self):
        '''
        複数選択されていなければマウス直下のパーツを選択する
        :return:
        '''
        cursor = QtGui.QCursor.pos()
        _ui = lib.get_show_repr()
        pos = QtCore.QPoint(cursor.x() - _ui['x'], cursor.y() - _ui['y'])
        # タブバーの高さを考慮 （ただ実際のタブの大きさと数ピクセルずれてる気がする
        self._context_pos = QtCore.QPoint(pos.x(), pos.y() - self.sizeHint().height())
        # パーツが矩形で選択されていなければマウス位置の下のボタンを選択しておく
        # 1個選択状態の場合は選択し直した方が直感的な気がする
        if len(self._selected) <= 1:
            _l = len(self._selected)
            _s = self._selected

            rect = QtCore.QRect(pos, pos)
            # ドッキングしてる状態だとタブの高さを考慮したほうがいい！？なんじゃこの挙動は…
            if self.isFloating() is False and self.dockArea() is not None:
                rect = QtCore.QRect(self._context_pos, self._context_pos)
            self._get_parts_in_rectangle(rect)
            if len(self._selected) > 1:
                self._selected = [self._selected[0]]
            if _l == 1 and len(self._selected) == 0:
                self._selected = _s
            self._set_stylesheet()
            self.repaint()

    def _draw_snap_gide(self):
        # スナップガイドの表示
        painter = QtGui.QPainter(self)
        color = QtGui.QColor(255, 255, 255, 40)
        pen = QtGui.QPen(color, )
        pen.setStyle(QtCore.Qt.DashDotLine)
        painter.setPen(pen)

        snap_unit_x = self._shelf_option.snap_width
        snap_unit_y = self._shelf_option.snap_height
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


class ShelfTabWeight(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ShelfTabWeight, self).__init__(parent)
        self.reference = None

    def get_all_parts_dict(self):
        # 指定のタブ以下にあるパーツを取得
        dict_ = {}
        # ボタンのデータ
        _b = []
        for child in self.findChildren(button.ButtonWidget):
            _b.append(vars(child.data))
        dict_['button'] = _b

        # 仕切り線のデータ
        _p = []
        for child in self.findChildren(partition.PartitionWidget):
            _p.append(vars(child.data))
        dict_['partition'] = _p

        return dict_

    def create_parts(self, data):
        if data.get('button') is not None:
            for _var in data['button']:
                # 辞書からインスタンスのプロパティに代入
                _d = button.ButtonData()
                for k, v in _var.items():
                    setattr(_d, k, v)
                button.create(self, _d)

        if data.get('partition') is not None:
            for _var in data['partition']:
                # 辞書からインスタンスのプロパティに代入
                _d = partition.PartitionData()
                for k, v in _var.items():
                    setattr(_d, k, v)
                partition.create(self, _d)

    def all_delete_parts(self):
        for child in self.findChildren(button.ButtonWidget):
            self.delete_parts(child)
        for child in self.findChildren(partition.PartitionWidget):
            self.delete_parts(child)

    def delete_parts(self, widget):
        widget.setParent(None)
        widget.deleteLater()
# #################################################################################################


def make_ui(load_file=None, edit_lock=False):
    # 同名のウインドウが存在したら削除
    ui = lib.get_ui(lib.TITLE, 'SiShelfWeight')
    if ui is not None:
        ui.close()

    app = QtWidgets.QApplication.instance()
    ui = SiShelfWeight(load_file=load_file, edit_lock=edit_lock)
    return ui


def quit_app():
    dict = lib.get_show_repr()
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


def popup():
    # マウス位置にポップアップ
    cursor = QtGui.QCursor.pos()
    main(x=cursor.x(), y=cursor.y())


def main(x=None, y=None, load_file=None, edit_lock=False):
    # 画面中央に表示
    ui = make_ui(load_file=load_file, edit_lock=edit_lock)
    _floating = lib.load_floating_data()
    if _floating:
        width = _floating['width']
        height = _floating['height']
    else:
        width = None
        height = None

    if lib.maya_api_version() > 201300:

        ui_script = "import sishelf.shelf;sishelf.shelf.restoration_workspacecontrol()"
        # 保存されたデータのウインドウ位置を使うとウインドウのバーが考慮されてないのでズレる
        opts = {
            "dockable": True,
            "floating": True,
            "width": width,
            "height": height,
            # 2017でのバグ回避のため area: left で決め打ちしてしまっているが
            # 2017未満ではrestoration_docking_ui で area を再設定するため問題ない
            # 2017 では workspace layout にどこにいるか等の実体がある
            "area": "left",
            "allowedArea": None,
            "x": x,
            "y": y,

            # below options have been introduced at 2017
            "widthSizingProperty": None,
            "heightSizingProperty": None,
            "initWidthAsMinimum": None,
            "retain": False,
            "plugins": None,
            "controls": None,
            "uiScript": ui_script,
            "closeCallback": None
        }

        ui.setDockableParameters(**opts)

        # 2017だとworkspaceControlコマンドでUI表示されるのでshowはいらない
        if lib.maya_api_version() > 201700:
            ui.show()

    else:
        # 2013
        ui.show()


def restoration_workspacecontrol():
    # workspacecontrolの再現用
    ui = make_ui()
    ui_script = "import sishelf.shelf;sishelf.shelf.restoration_workspacecontrol()"
    # 保存されたデータのウインドウ位置を使うとウインドウのバーが考慮されてないのでズレる
    opts = {
        "dockable": True,
        "floating": False,
        "area": "left",
        "allowedArea": None,
        "x": None,
        "y": None,
        # below options have been introduced at 2017
        "widthSizingProperty": None,
        "heightSizingProperty": None,
        "initWidthAsMinimum": None,
        "retain": False,
        "plugins": None,
        "controls": None,
        "uiScript": ui_script,
        "closeCallback": None
    }
    ui.setDockableParameters(**opts)


if __name__ == '__main__':
    main()

#-----------------------------------------------------------------------------
# EOF
#-----------------------------------------------------------------------------
