# -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
from . import button_setting
from . import button
from . import partition
from . import partition_setting
from . import lib
from . import shelf_option
from . import xpop
from . import multi_edit
from . import synoptic

import json
import os
import os.path
import pymel.core as pm
import maya.cmds as cmds
import re
import copy

if lib.maya_version() < 2015:
    # 2014以下のバージョン用
    MayaQWidgetDockableMixin = object

elif lib.maya_version() < 2017:
    from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

elif 2017 <= lib.maya_version() < 2019:
    # TODO: 新バージョンが出たら確認すること
    from .patch import m2017
    MayaQWidgetDockableMixin = m2017.MayaQWidgetDockableMixin2017
else:
    from maya.app.general.mayaMixin import MayaQWidgetDockableMixin


class SiShelfWidget(MayaQWidgetDockableMixin, QtWidgets.QTabWidget):
    URL = "https://github.com/mochio326/SiShelf"
    VAR = '1.7.3'
    PEN_WIDTH = 1  # 矩形の枠の太さ

    def __init__(self, parent=None, load_file=None, edit_lock=False):
        super(SiShelfWidget, self).__init__(parent)
        # メモリ管理的おまじない
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

        self.band = None
        self.right_drag_rect = None
        self.right_drag = False
        self.parts_moving = False
        self.parts_resizing = False
        self.multi_edit_view = None
        self.select_parts_script_job = None
        self.selected = None
        self.reset_selected()

        self._origin = None
        # self._floating_save = False
        self._clipboard = None
        self._context_pos = QtCore.QPoint()
        self._cut_flag = False
        self._shelf_option = shelf_option.OptionData()
        self._operation_history = [self._get_all_tab_data()]
        self._current_operation_history = 0
        self._parts_resize_mode = None

        self.set_stylesheet()
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.currentChanged.connect(self._current_tab_change)
        self.tabBar().tabMoved.connect(self._tab_moved)
        self._regeneration_all_tab()

        # self.installEventFilter(self)

    def _current_tab_change(self):
        self.reset_selected()
        self.set_stylesheet()
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
            _tb.addSeparator()
            if self.currentWidget().reference is None:
                _tb.addAction('Export', self._export_tab)
                _tb.addAction('Import', self._import_tab)
                _tb.addSeparator()
                _tb.addAction('External reference', self._reference_tab)  # 外部参照設定
            else:
                _tb.addAction('Remove external reference', self._remove_reference_tab)  # 外部参照設定解除

            _df = _menu.addMenu('Default setting')
            _df.addAction('Button', self._button_default_setting)
            _df.addAction('Partition', self._partition_default_setting)
            if self.currentWidget().reference is None:
                _menu.addAction('XPOP setting', self._xpop_setting)

            _menu.addSeparator()
            _menu.addAction('Option', self._option)
        _menu.addAction('Version information', self._info)

        self._select_cursor_pos_parts()
        # マウス位置に出現
        cursor = QtGui.QCursor.pos()
        _menu.exec_(cursor)
        if self.right_drag:
            self.right_drag = False
            self.band = None
            self.repaint()

    def _info(self):
        QtWidgets.QMessageBox.information(
            self, 'Version information',
            'SiShelf ' + self.VAR,
            QtWidgets.QMessageBox.Ok,
            QtWidgets.QMessageBox.Ok
        )

    def _option(self):
        self._shelf_option = shelf_option.OptionDialog.open(self)
        self.set_stylesheet()

    def _copy(self):
        self._clipboard = copy.deepcopy(self.selected[0].data)

    def _paste(self):
        if self._clipboard is None:
            return
        data = copy.deepcopy(self._clipboard)
        data.position = self._context_pos

        if isinstance(data, button.ButtonData):
            button.create(self.currentWidget(), data)
        elif isinstance(data, partition.PartitionData):
            partition.create(self.currentWidget(), data)

        self.reset_selected()
        self.repaint()
        self.save_all_tab_data()
        self.set_stylesheet()
        # カットの場合は貼り付けは一度だけ
        if self._cut_flag is True:
            self._clipboard = None
            self._cut_flag = False

    def _cut(self):
        self._copy()
        self.delete_parts(self.selected[0])
        self.reset_selected()
        self._cut_flag = True

    def _delete(self):
        for s in self.selected:
            self.delete_parts(s)
        self.reset_selected()
        self.save_all_tab_data()

    def _edit(self):
        if len(self.selected) != 1:
            # print('Only standalone selection is supported.')
            if self.multi_edit_view is None:
                self.multi_edit_view = multi_edit.MultiEditorDialog(self)
                self.multi_edit_view.sync_list()
                self.multi_edit_view.show()
            return
        parts = self.selected[0]

        if isinstance(parts.data, button.ButtonData):
            data, _result = button_setting.SettingDialog.get_data(self, parts.data)
            if _result is not True:
                print("Cancel.")
                return None
            parts.data = data
            button.update(parts, parts.data)

        elif isinstance(parts.data, partition.PartitionData):
            data, _result = partition_setting.SettingDialog.get_data(self, parts.data)
            if _result is not True:
                print("Cancel.")
                return None
            parts.data = data

        '''
        XPOPの為にウィジェットの順番を変えたくないので、utton.updateにてボタンの描画設定を変更してみたものの
        縦横サイズ固定でない場合、ボタンのサイズが適切に変化しなかった。
        その対策として、全てのパーツを作り直すことでこれを回避している。
        '''
        # self.repaint()
        self.current_tab_widget_refresh()

    def _add_button(self):
        data = button.get_default()
        data.position = self._context_pos
        if self.right_drag:
            data.position_x = self.right_drag_rect.x()
            data.position_y = self.right_drag_rect.y() - self.sizeHint().height()

            _w = self.right_drag_rect.width()
            _h = self.right_drag_rect.height()
            if _w != 1 and _h != 1:
                data.width = _w
                data.height = _h
            if self._shelf_option.snap_active:
                if _w == 0:
                    data.width = self._shelf_option.snap_width
                if _h == 0:
                    data.height = self._shelf_option.snap_height

            data.size_flag = True

        self.create_button(data)
        self.save_all_tab_data()
        self.set_stylesheet()

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
        self.reset_selected()
        self.repaint()
        return data

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

    def _xpop_setting(self):
        _w = self.currentWidget()
        ls = _w.get_all_button()
        parts, _result = xpop.XpopSettingDialog.show_dialog(self, ls)
        if _result is not True:
            print("Cancel.")
            return None
        _w.delete_all_button()
        _w.create_button_from_instance(parts)
        self.set_stylesheet()
        self.save_all_tab_data()

    def _undo(self):
        self._undo_redo_base('undo')

    def _redo(self):
        self._undo_redo_base('redo')

    def _undo_redo_base(self, type):
        if type == 'undo':
            _add = 1
        else:
            _add = -1

        if self._current_operation_history >= len(self._operation_history) - _add:
            return
        if self._current_operation_history + _add < 0:
            return

        self._current_operation_history = self._current_operation_history + _add
        data = self._operation_history[self._current_operation_history]
        self._regeneration_all_tab(data)

    # -----------------------
    # Tab
    # -----------------------
    def _regeneration_all_tab(self, data=None, save_history=False):
        # 作ったばかりのタブの関数が動作しないことがなぜかあるので、その場合用にタブを作り直す
        if data is None:
            data = self._get_all_tab_data()
        self.currentChanged.disconnect()
        self._delete_all_tab()
        self._make_json_data_to_tab(data)
        self.currentChanged.connect(self._current_tab_change)
        self.set_stylesheet()
        self.save_all_tab_data(save_history=save_history)

    def _delete_all_tab(self):
        # 逆順で消さないとタブが残る
        _tab_count = self.count()
        for _c in range(_tab_count)[::-1]:
            self.removeTab(_c)

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
            # ここで記録しなくても消した後のtab changeで記録されるので問題なし
            # self.save_all_tab_data()
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
        self.insertTab(self.count() + 1, ShelfTabWidget(), new_tab_name)
        self.setCurrentIndex(self.count() + 1)
        self.save_all_tab_data()
        self._regeneration_all_tab()

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
            self.current_tab_widget_refresh(new_widget_data=_data)

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
        self.current_tab_widget_refresh(new_widget_data=_data)

    def _remove_reference_tab(self):
        if self.currentWidget().reference is not None:
            self.currentWidget().reference = None
            self.current_tab_widget_refresh(delete_widget=True)
            self.setTabIcon(self.currentIndex(), QtGui.QIcon())

    # -----------------------
    # Save Load
    # -----------------------
    def _get_save_file_path(self):
        if self.load_file is None:
            path = lib.get_tab_data_path()
        else:
            path = self.load_file
        return path

    def _make_json_data_to_tab(self, data):
        for _vars in data:
            tab_number = self.count()
            self.insertTab(tab_number, ShelfTabWidget(), _vars['name'])

            if _vars['current'] is True:
                self.setCurrentIndex(tab_number)
            if _vars.get('reference') is None:
                self.widget(tab_number).create_parts_from_dict(_vars)
            else:
                if _vars['reference'] is None:
                    self.widget(tab_number).create_parts_from_dict(_vars)
                else:
                    icon = QtGui.QIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowDown))
                    self.setTabIcon(tab_number, icon)
                    _data = lib.not_escape_json_load(_vars['reference'])
                    self.widget(tab_number).reference = _vars['reference']
                    self.widget(tab_number).delete_all_parts()
                    self.widget(tab_number).create_parts_from_dict(_data)

    def load_all_tab_data(self):
        path = self._get_save_file_path()
        data = lib.not_escape_json_load(path)
        if data is None:
            self.insertTab(0, ShelfTabWidget(), 'Tab1')
            return
        self._make_json_data_to_tab(data)

    def _get_all_tab_data(self):
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
        return ls

    def save_all_tab_data(self, save_history=True):
        if self.edit_lock is True:
            return

        ls = self._get_all_tab_data()
        lib.make_save_dir()
        path = self._get_save_file_path()
        lib.not_escape_json_dump(path, ls)

        if self.multi_edit_view is not None:
            self.multi_edit_view.sync_list()

        if not save_history:
            return
        # Undo Redo用の操作
        if self._current_operation_history > 0:
            del self._operation_history[0:self._current_operation_history]
        self._operation_history.insert(0, ls)
        self._current_operation_history = 0

    def reset_selected(self):
        self.selected = []

    def get_button_widgets(self):
        return self.currentWidget().findChildren(button.ButtonWidget)

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
            modifiers = QtWidgets.QApplication.keyboardModifiers()

            if len(self.selected) > 1:
                # 複数選択されていたらまとめて移動を優先
                if modifiers == QtCore.Qt.ControlModifier:
                    # リサイズ
                    self._selected_parts_resize(event.pos(), False, False)
                else:
                    self._selected_parts_move(event.pos(), False, False)
            else:
                if modifiers == QtCore.Qt.ControlModifier:
                    # リサイズ
                    self._parts_resize(event.source(), event.pos())
                else:
                    self._parts_move(event.source(), event.pos())

                self.save_all_tab_data()
                self._origin = QtCore.QPoint()

            # よくわからん
            event.setDropAction(QtCore.Qt.MoveAction)
            event.accept()

        self.parts_moving = False
        self.parts_resizing = False
        self.repaint()

    def dragMoveEvent(self, event):
        if self.edit_lock is True or self.currentWidget().reference is not None:
            return
        # パーツを移動中の描画更新
        if len(self.selected) > 0:
            if self.parts_resizing:
                # リサイズ
                self._selected_parts_resize(event.pos(), False, False)
            if self.parts_moving:
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

        self.parts_resizing = False
        self.parts_moving = False
        self._offset_position_change = False
        self._scale_change = False

        self._origin = event.pos()

        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.AltModifier:
            # 画面全体の移動
            if event.button() == QtCore.Qt.MiddleButton:
                self._offset_position_change = True
                _cw = self.currentWidget()
                self._offset_position_x_temp = _cw.position_offset_x
                self._offset_position_y_temp = _cw.position_offset_y
                self.band = None
                return
            # 画面全体の表示スケール変更
            if event.button() == QtCore.Qt.RightButton:
                self._scale_change = True
                _cw = self.currentWidget()
                self._offset_position_x_temp = _cw.position_offset_x
                self._offset_position_y_temp = _cw.position_offset_y
                self._scale_temp = _cw.scale
                self.band = None
                return

        if event.button() == QtCore.Qt.LeftButton:
            self.band = QtCore.QRect()
            self.right_drag = False

        if event.button() == QtCore.Qt.MiddleButton:

            self._select_cursor_pos_parts()
            if len(self.selected) <= 1:
                self.set_stylesheet()

            modifiers = QtWidgets.QApplication.keyboardModifiers()
            if modifiers == QtCore.Qt.ControlModifier:
                self.parts_resizing = True
                self._parts_resize_mode = button.resize_mode
            else:
                self.parts_moving = True

        if event.button() == QtCore.Qt.RightButton:
            # スナップ機能の際は開始位置をいい感じに加工
            self._origin = self.__right_drag_snap_pos(self._origin)
            self.band = QtCore.QRect()
            self.right_drag = True

        self.repaint()

    def __right_drag_snap_pos(self, pos, mode='rect'):
        if mode == 'rect':
            _offset_pixel = -0
        elif mode == 'create':
            _offset_pixel = -1

        # スナップ機能の際は終了位置をいい感じに加工
        if self._shelf_option.snap_active:
            _x = int(pos.x() / self._shelf_option.snap_width) * self._shelf_option.snap_width
            _y = int(pos.y() / self._shelf_option.snap_height) * self._shelf_option.snap_height
            pos = QtCore.QPoint(_x + _offset_pixel, _y + self.sizeHint().height() + _offset_pixel)
        return pos

    def mouseMoveEvent(self, event):
        if self.edit_lock is True or self.currentWidget().reference is not None:
            return

        if self.band is not None:
            pos = event.pos()
            if self.right_drag:
                # スナップ機能の際は終了位置をいい感じに加工
                pos = self.__right_drag_snap_pos(pos)
            self.band = QtCore.QRect(self._origin, pos)

        else:
            # パーツを移動中の描画更新
            if len(self.selected) > 0:
                if self.parts_resizing:
                    # リサイズ
                    self._selected_parts_resize(event.pos(), False, False)
                if self.parts_moving:
                    self._selected_parts_move(event.pos(), False, False)

        if self._offset_position_change:
            _x = self._origin.x() - event.pos().x()
            _y = self._origin.y() - event.pos().y()
            _cw = self.currentWidget()
            _cw.position_offset_x = int(self._offset_position_x_temp - _x)
            _cw.position_offset_y = int(self._offset_position_y_temp - _y)
            _cw.set_move_and_scale()

        if self._scale_change:
            # 仮。正式には移動距離をとる
            _x = self._origin.x() - event.pos().x()
            _cw = self.currentWidget()
            _cw.scale = self._scale_temp + 0.01 * _x
            # ドラッグしたポイントを基準に拡縮するためのいい感じの式
            _cw.position_offset_x = self._offset_position_x_temp + self._origin.x() * (self._scale_temp - _cw.scale)
            _cw.position_offset_y = self._offset_position_y_temp + (self._origin.y() - self.sizeHint().height()) * (self._scale_temp - _cw.scale)
            _cw.set_move_and_scale()

        self.repaint()

    def mouseReleaseEvent(self, event):

        if self.edit_lock is True or self.currentWidget().reference is not None:
            return

        if event.button() == QtCore.Qt.LeftButton:
            if not self._origin:
                self._origin = event.pos()
            rect = QtCore.QRect(self._origin, event.pos()).normalized()
            self._get_parts_in_rectangle(rect)
            self.set_stylesheet()
            self.band = None

        # 選択中のパーツを移動/リサイズ
        # ボタン上でドラッグした場合にはQtCore.Qt.NoButtonが戻ってくる
        if event.button() == QtCore.Qt.MiddleButton or event.button() == QtCore.Qt.NoButton:
            if self.parts_resizing:
                # リサイズ
                self._selected_parts_resize(event.pos())
            if self.parts_moving:
                # 移動
                self._selected_parts_move(event.pos())

            self.save_all_tab_data()

        if event.button() == QtCore.Qt.RightButton:
            if not self._origin:
                self._origin = self.__right_drag_snap_pos(event.pos(), mode='create')
            pos = self.__right_drag_snap_pos(event.pos(), mode='create')
            rect = QtCore.QRect(self._origin, pos).normalized()
            self.right_drag_rect = rect

        self._origin = QtCore.QPoint()
        self.parts_moving = False
        self.parts_resizing = False
        self.repaint()

        if self.multi_edit_view is not None:
            self.multi_edit_view.parent_select_synchronize()

    def paintEvent(self, event):
        _cw = self.currentWidget()
        # 矩形範囲、スナップガイドの描画（必要な時だけ上部に描画）
        if self.band is not None or self.parts_moving or self.parts_resizing or self.right_drag:
            _cw.create_guide_widget()
        else:
            _cw.delete_guide_widget()

    def eventFilter(self, obj, event):
        print event.type()
        return False

    def hideEvent(self, event):
        if not cmds.scriptJob(ex=self.select_parts_script_job):
            return
        cmds.scriptJob(kill=self.select_parts_script_job, force=True)
        self.select_parts_script_job = None
        if self.edit_lock is False:
            if lib.maya_version() < 2017:
                lib.floating_save(self)
                #if self._floating_save is False:
                #    lib.floating_save(self)
                #self._floating_save = True

    def showEvent(self, event):
        if self.select_parts_script_job is not None:
            return
        self.select_parts_script_job = cmds.scriptJob(e=["SelectionChanged", lambda: self.set_stylesheet()],
                                                      protected=True)

    def closeEvent(self, event):
        self.hideEvent(event)
        # superだと2017でエラーになったため使用中止
        # super(SiShelfWidget, self).closeEvent(event)
        QtWidgets.QWidget.close(self)

    def keyPressEvent(self, event):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ControlModifier:
            if event.key() == QtCore.Qt.Key_C:
                self._copy()
                return
            if event.key() == QtCore.Qt.Key_V:
                self._paste()
                return
            if event.key() == QtCore.Qt.Key_X:
                self._cut()
                return
            if event.key() == QtCore.Qt.Key_Z:
                self._undo()
                return
            if event.key() == QtCore.Qt.Key_Y:
                self._redo()
                return

        if event.key() == QtCore.Qt.Key_Delete:
            self._delete()
            return

    # -----------------------
    # Others
    # -----------------------
    def current_tab_widget_refresh(self, delete_widget=False, new_widget_data=None):
        if new_widget_data is None:
            data = self.currentWidget().get_all_parts_dict()
        else:
            data = new_widget_data

        self.currentWidget().delete_all_parts()

        if not delete_widget:
            self.currentWidget().create_parts_from_dict(data)
        self.set_stylesheet()
        self.save_all_tab_data()

    def _selected_parts_resize(self, after_pos, save=True, data_pos_update=True):
        if self._parts_resize_mode is None:
            return
        # 選択中のパーツをリサイズ
        if len(self.selected) > 0:
            for p in self.selected:
                self._parts_resize(p, after_pos, data_pos_update)
            if save is True:
                self._origin = QtCore.QPoint()
                self.save_all_tab_data()

    def _parts_resize(self, parts, after_pos, data_pos_update=True):
        if self._parts_resize_mode is None:
            return

        _parts_x = parts.data.position.x()
        _parts_y = parts.data.position.y()
        _parts_w = parts.data.size.width()
        _parts_h = parts.data.size.height()

        # ドラッグ中に移動した相対位置を加減算してリサイズ
        _rect = QtCore.QRect(self._origin, after_pos)
        if 'right' in self._parts_resize_mode:
            _parts_w += _rect.width()
        if 'left' in self._parts_resize_mode:
            _parts_w -= _rect.width()
            _parts_x += _rect.width()
        if 'bottom' in self._parts_resize_mode:
            _parts_h += _rect.height()
        if 'top' in self._parts_resize_mode:
            _parts_y += _rect.height()
            _parts_h -= _rect.height()

        # サイズがマイナスになるとボタンが反転するような動きになるようにする
        _flip_w = False
        _flip_h = False

        if _parts_w < 0:
            _flip_w = True
            _parts_w = abs(_parts_w)
            if 'right' in self._parts_resize_mode:
                _parts_x += _rect.width() + _parts_w
            if 'left' in self._parts_resize_mode:
                _parts_x -= _rect.width() - _parts_w
        if _parts_h < 0:
            _flip_h = True
            _parts_h = abs(_parts_h)
            if 'bottom' in self._parts_resize_mode:
                _parts_y += _rect.height() + _parts_h
            if 'top' in self._parts_resize_mode:
                _parts_y -= _rect.height() - _parts_h

        # スナップ時の計算。フリップしたかどうかでちょっとずつ計算変わる。。。
        _cw = self.currentWidget()
        if self._shelf_option.snap_active is True:
            # 位置は固定、横幅だけ変化
            def resize_w():
                _x, _ = _cw.get_nearest_position(after_pos.x(), None)
                w = _x - parts.data.position.x()
                if w == 0:
                    w = _cw.snap_unit_x
                return w

            # 位置も横幅も変化
            def resize_x():
                x, _ = _cw.get_nearest_position(after_pos.x(), None)
                if x == parts.data.position.x():
                    x -= _cw.snap_unit_x
                w = parts.data.position.x() - x
                return x, w

            # 位置は固定、縦幅だけ変化
            def resize_h():
                _, _y = _cw.get_nearest_position(None, after_pos.y())
                h = _y - parts.data.position.y()
                if h == 0:
                    h = _cw.snap_unit_y
                return h

            # 位置も縦も変化
            def resize_y():
                _, y = _cw.get_nearest_position(None, after_pos.y())
                if parts.data.position.y() == y:
                    y -= _cw.snap_unit_y
                h = parts.data.position.y() - y
                return y, h

            if 'right' in self._parts_resize_mode:
                if _parts_x != parts.data.position.x():
                    _parts_x, _parts_w = resize_x()
                else:
                    _parts_w = resize_w()

            if 'left' in self._parts_resize_mode:
                if _parts_x != parts.data.position.x() and _flip_w is False:
                    _parts_x, _parts_w = resize_x()
                else:
                    _parts_w = resize_w()

            if 'bottom' in self._parts_resize_mode:
                if _parts_y != parts.data.position.y():
                    _parts_y, _parts_h = resize_y()
                else:
                    _parts_h = resize_h()

            if 'top' in self._parts_resize_mode:
                if _parts_y != parts.data.position.y() and _flip_h is False:
                    _parts_y, _parts_h = resize_y()
                    _parts_h += parts.data.size.height()
                else:
                    _parts_h = resize_h()

        parts.move(QtCore.QPoint(_parts_x, _parts_y))
        parts.setFixedSize(_parts_w, _parts_h)

        if data_pos_update:
            parts.data.position = QtCore.QPoint(_parts_x, _parts_y)
            parts.data.size = QtCore.QSize(_parts_w, _parts_h)

    def _selected_parts_move(self, after_pos, save=True, data_pos_update=True):
        # 選択中のパーツを移動
        if len(self.selected) > 0:
            for p in self.selected:
                self._parts_move(p, after_pos, data_pos_update)
            if save is True:
                self._origin = QtCore.QPoint()
                self.save_all_tab_data()

    def _parts_move(self, parts, after_pos, data_pos_update=True):
        # ドラッグ中に移動した相対位置を加算
        _rect = QtCore.QRect(self._origin, after_pos)
        _p = parts.data.position
        _x = _p.x() + _rect.width()
        _y = _p.y() + _rect.height()

        if self._shelf_option.snap_active is True:
            _x, _y = self.currentWidget().get_nearest_position(_x, _y)

        _position = QtCore.QPoint(_x, _y)
        parts.move(_position)
        if data_pos_update is True:
            parts.data.position = _position

    def _get_parts_in_rectangle(self, rect):
        self.reset_selected()
        chidren = []
        chidren.extend(self.currentWidget().findChildren(button.ButtonWidget))
        chidren.extend(self.currentWidget().findChildren(partition.PartitionWidget))

        for child in chidren:
            # 矩形内に位置しているかを判定
            if rect.intersects(self._get_parts_absolute_geometry(child)) is False:
                continue
            self.selected.append(child)

        # ウィジェット選択とノード選択を同期
        select_nodes = []
        for _s in self.selected:
            if not isinstance(_s, button.ButtonWidget):
                continue
            if _s.data.type_ != 2:
                continue
            select_nodes.extend(_s.data.select_parts.split(','))
        synoptic.node_select(select_nodes)

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

        # タブ
        css += 'QTabBar::tab { ' \
                'height: ' + str(self._shelf_option.tab_height) + 'px;' \
                'font-size: ' + str(self._shelf_option.tab_label_size) + 'pt;' \
                '}'

        # ボタン
        buttons = self.currentWidget().findChildren(button.ButtonWidget)
        css = lib.button_css(buttons, css)

        # 選択中のパーツを誇張
        if self.edit_lock is True:
            pass
        elif self.currentWidget().reference is None:
            for s in self.selected:
                css += '#' + s.objectName() + '{'
                if isinstance(s.data, button.ButtonData):
                    if s.data.use_bgcolor is True:
                        css += 'background:' + s.data.bgcolor + ';'
                css += 'border-color:red; border-style:solid; border-width:1px;}'

            # synopticボタンの装飾
            for b in buttons:
                if b.data.type_ != 2:
                    continue
                css += '#' + b.objectName() + '{border-radius: 10px;}'
                _c = b.selected_node_check()
                if _c == 1:
                    # 一部選択れている
                    css += '#' + b.objectName() + '{border-color:orange; border-style:solid; border-width:2px;}'
                elif _c == 2:
                    # 全て選択れている
                    css += '#' + b.objectName() + '{border-color:yellow; border-style:solid; border-width:2px;}'

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

        if len(self.selected) > 1:
            return

        # パーツが矩形で選択されていなければマウス位置の下のボタンを選択しておく
        # 1個選択状態の場合は選択し直した方が直感的な気がする
        _l = len(self.selected)
        _s = self.selected

        rect = QtCore.QRect(pos, pos)
        # ドッキングしてる状態だとタブの高さを考慮したほうがいい！？なんじゃこの挙動は…
        if self.isFloating() is False and self.dockArea() is not None:
            rect = QtCore.QRect(self._context_pos, self._context_pos)
        self._get_parts_in_rectangle(rect)
        if len(self.selected) > 1:
            self.selected = [self.selected[0]]
        if _l == 1 and len(self.selected) == 0:
            self.selected = _s
        self.set_stylesheet()
        self.repaint()

        if self.multi_edit_view is not None:
            self.multi_edit_view.parent_select_synchronize()


class ShelfBackgroundImage(QtWidgets.QLabel):
    def __init__(self, filename=None, parent=None):
        super(ShelfBackgroundImage, self).__init__(parent)
        self.scale = 1
        self.pixmap = QtGui.QPixmap(filename)
        self.set_image()
        self.set_scale(self.scale)

    def set_image(self):
        self.setPixmap(self.pixmap)

    def set_scale(self, scale):
        self.scale = scale
        _w = self.pixmap.width() * self.scale
        _h = self.pixmap.height() * self.scale
        _p = self.pixmap.scaled(_w, _h, QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.FastTransformation)
        self.setPixmap(_p)
        self.setFixedSize(QtCore.QSize(_w, _h))


def _get_parent_shelf_widget(widget):
    return lib.get_any_parent_widget(widget, SiShelfWidget)


class GuidePaintWidget(QtWidgets.QWidget):
    PEN_WIDTH = 1

    def __init__(self, parent=None):
        super(GuidePaintWidget, self).__init__(parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.shelf = _get_parent_shelf_widget(self)
        self._shelf_option = shelf_option.OptionData()
        self.band_temp = None

    def paintEvent(self, event):
        # 矩形範囲の描画
        if self.shelf.band is not None:
            self.band_temp = copy.deepcopy(self.shelf.band)
            self.band_temp.setY(self.band_temp.y() - self._shelf_option.tab_height - 2)
            self.band_temp.setHeight(self.band_temp.height() - self._shelf_option.tab_height - 2)

            painter = QtGui.QPainter(self)
            color = QtGui.QColor(255, 255, 255, 125)
            pen = QtGui.QPen(color, self.PEN_WIDTH)
            painter.setPen(pen)
            if self.shelf.right_drag:
                painter.setBrush(QtGui.QBrush(QtCore.Qt.lightGray, QtCore.Qt.BDiagPattern))
            painter.drawRect(self.band_temp)
            painter.restore()

        # ガイドグリッドの描画
        if self.shelf.parts_moving or self.shelf.parts_resizing or self.shelf.right_drag:
                if self._shelf_option.snap_active and self._shelf_option.snap_grid:
                    self._draw_snap_gide()

    def _draw_snap_gide(self):
        # スナップガイドの表示
        painter = QtGui.QPainter(self)
        color = QtGui.QColor(255, 255, 255, 40)
        pen = QtGui.QPen(color, )
        pen.setStyle(QtCore.Qt.DashDotLine)
        painter.setPen(pen)

        x, y = self.parent().get_snap_position_list()

        # 横線
        for _p in y:
            line = QtCore.QLine(QtCore.QPoint(0, _p), QtCore.QPoint(self.width(), _p))
            painter.drawLine(line)
        # 縦線
        for _p in x:
            line = QtCore.QLine(QtCore.QPoint(_p, 0), QtCore.QPoint(_p, self.height()))
            painter.drawLine(line)
        painter.restore()


class ShelfTabWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(ShelfTabWidget, self).__init__(parent)
        self.reference = None
        self.bg_widget = None
        self.guide_widget = None
        self.layout = None
        self.scale = 1
        self.position_offset_x = 0
        self.position_offset_y = 0
        self._shelf_option = shelf_option.OptionData()

    def get_snap_position_list(self):
        x = []
        y = []
        # 横
        _u_y = self.snap_unit_y
        for i in range(self.height() / _u_y + 1):
            y.append(int(round(_u_y * i + self.position_offset_y % _u_y)))
        # 縦
        _u_x = self.snap_unit_x
        for i in range(self.width() / _u_x + 1):
            x.append(int(round(_u_x * i + self.position_offset_x % _u_x)))
        return x, y

    def get_nearest_position(self, pos_x=None, pos_y=None):
        x_list, y_list = self.get_snap_position_list()
        return self._get_nearest_value(pos_x, x_list), self._get_nearest_value(pos_y, y_list)

    # リスト内から一番近い数値を返す　numpyが使えればもっと簡潔になるのに(´；ω；`)
    def _get_nearest_value(self, value, int_list):
        if value is None:
            return None
        int_list.sort()
        if min(int_list) > value:
            return min(int_list)
        if max(int_list) < value:
            return max(int_list)
        for i in range(len(int_list)):
            if int_list[i] > value or int_list[i + 1] < value:
                continue
            min_difference = abs(value - int_list[i])
            max_difference = abs(int_list[i + 1] - value)
            if min_difference < max_difference:
                return int_list[i]
            else:
                return int_list[i + 1]

    snap_unit_x = property(doc='snap_unit_x property')
    @snap_unit_x.getter
    def snap_unit_x(self):
        return int(self._shelf_option.snap_width * self.scale)

    snap_unit_y = property(doc='snap_unit_y property')
    @snap_unit_y.getter
    def snap_unit_y(self):
        return int(self._shelf_option.snap_height * self.scale)

    def get_all_parts_dict(self):
        # 指定のタブ以下にあるパーツを取得
        dict_ = {}
        # ボタンのデータ
        _b = []
        _ls = self.get_all_button()
        for child in _ls:
            _b.append(child.get_save_dict())
        dict_['button'] = _b

        # 仕切り線のデータ
        _p = []
        _ls = self.get_all_partition()
        for child in _ls:
            _p.append(child.get_save_dict())
        dict_['partition'] = _p
        return dict_

    def create_parts_from_dict(self, data):
        #if data.get('bgimage') is not None:
        self.bg_widget = ShelfBackgroundImage(r'C:\temp\vessel\shelf_bg.jpg', self)
        self.bg_widget.show()

        if data.get('button') is not None:
            for _var in data['button']:
                # 辞書からインスタンスのプロパティに代入
                _d = button.ButtonData()
                for k, v in _var.items():
                    setattr(_d, k, v)
                _d.scale = self.scale
                button.create(self, _d)

        if data.get('partition') is not None:
            for _var in data['partition']:
                # 辞書からインスタンスのプロパティに代入
                _d = partition.PartitionData()
                for k, v in _var.items():
                    setattr(_d, k, v)
                _d.scale = self.scale
                partition.create(self, _d)

    def create_guide_widget(self):
        if self.guide_widget is None:
            self.guide_widget = GuidePaintWidget(self)
            self.guide_widget.setFixedSize(QtCore.QSize(self.width(), self.height()))
            self.guide_widget.show()

    def delete_guide_widget(self):
        if self.guide_widget is not None:
            self.guide_widget.setParent(None)
            self.guide_widget.deleteLater()
            self.guide_widget = None

    def create_button_from_instance(self, ls):
        for _l in ls:
            button.create(self, _l)

    def delete_all_parts(self):
        self.delete_all_button()
        self.delete_all_partition()

    def delete_all_button(self):
        for child in self.findChildren(button.ButtonWidget):
            self.delete_parts(child)

    def delete_all_partition(self):
        for child in self.findChildren(partition.PartitionWidget):
            self.delete_parts(child)

    def get_all_button(self):
        ls = []
        for child in self.findChildren(button.ButtonWidget):
            # 子widget上でドラッグイベントを開始した際などに位置・サイズの情報が伝達しない場合があるようなので
            # ここで入れなおしておく
            '''
            child.data.position_x = child.x()
            child.data.position_y = child.y()
            child.data.width = child.width()
            child.data.height = child.height()
            '''
            #child.data.position = child
            #child.data.size = child
            ls.append(child.data)
        return ls

    def get_all_partition(self):
        ls = []
        for child in self.findChildren(partition.PartitionWidget):
            # 子widget上でドラッグイベントを開始した際などに位置・サイズの情報が伝達しない場合があるようなので
            # ここで入れなおしておく
            # child.data.position_x = child.x()
            # child.data.position_y = child.y()
            # child.data.width = child.width()
            # child.data.height = child.height()
            ls.append(child.data)
        return ls

    def set_move_and_scale(self):
        if self.bg_widget is not None:
            self.bg_widget.move(QtCore.QPoint(self.position_offset_x , self.position_offset_y))
            self.bg_widget.set_scale(self.scale)

        for _w in self.findChildren(button.ButtonWidget):
            _w.data.temp_scale = self.scale
            _w.data.temp_position_offset_x = self.position_offset_x
            _w.data.temp_position_offset_y = self.position_offset_y
            button.update(_w, _w.data)
        for _w in self.findChildren(partition.PartitionWidget):
            _w.data.temp_scale = self.scale
            _w.data.temp_position_offset_x = self.position_offset_x
            _w.data.temp_position_offset_y = self.position_offset_y
            partition.update(_w, _w.data)

        self.repaint()

    def delete_parts(self, widget):
        widget.setParent(None)
        widget.deleteLater()

# #################################################################################################

def make_ui(load_file=None, edit_lock=False):
    # 同名のウインドウが存在したら削除
    ui = lib.get_ui(lib.TITLE, 'SiShelfWidget')
    if ui is not None:
        ui.close()

    app = QtWidgets.QApplication.instance()
    ui = SiShelfWidget(load_file=load_file, edit_lock=edit_lock)
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
        window = SiShelfWidget()
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
    ui.show()

    _floating = lib.load_floating_data()
    if _floating:
        width = _floating['width']
        height = _floating['height']
    else:
        width = None
        height = None

    if lib.maya_version() > 2013:

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


def restoration_workspacecontrol():
    # workspacecontrolの再現用
    ui = make_ui()
    ui.show()
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
