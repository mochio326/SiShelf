# -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
from . import lib
from . import button
import sys
# from __future__ import absolute_import, division, print_function

SORT_ROLE = QtCore.Qt.UserRole + 1


class Column(object):
    u"""カラム情報"""

    def __init__(self, index, value):
        self.value = value
        self.index = index


class Columns(object):
    u"""インスタンス変数のColumnクラスのものを抽出してcolumnsメソッドで取得できるクラス"""

    def __init__(self):
        self._columns = None

    @property
    def columns(self):
        if self._columns is None:
            self._columns = self._get_columns()
        return self._columns

    def _get_columns(self):
        tmp_columns = []
        for k, v in self.__dict__.items():
            if type(v) == Column:
                tmp_columns.append(v)
        return sorted(tmp_columns, key=lambda x: x.index)


class ButtonInfo(Columns):
    u"""ファイル情報"""
    # header = ['label', 'position_x', 'position_y', 'width', 'height', 'label_font_size', 'tooltip', 'bool_tooltip',
    # 'icon_file', 'use_icon', 'icon_style', 'bgcolor', 'use_bgcolor', 'label_color', 'use_label_color']
    header = ['label', 'x', 'y', 'width', 'height']

    row_count = len(header)

    def __init__(self, button):
        u"""initialize
        :param path: ファイルパス
        :type path: unicode
        """
        super(ButtonInfo, self).__init__()
        self.widget = button
        _data_dict = button.data.get_save_dict()
        '''
        for index, item in enumerate(self.header):
            self.__dict__[item] = Column(index, dict.get(item))

        '''
        self.label = Column(0, _data_dict.get('label'))
        self.position_x = Column(1, _data_dict.get('position_x'))
        self.position_y = Column(2, _data_dict.get('position_y'))
        self.width = Column(3, _data_dict.get('width'))
        self.height = Column(4, _data_dict.get('height'))

    def widget_data_refresh(self):
        for item in self.__dict__:
            if not isinstance(self.__dict__[item], Column):
                continue
            self.widget.data.__dict__[item] = self.__dict__[item].value
            button.update(self.widget, self.widget.data)


class EditTableModel(QtCore.QAbstractTableModel):
    def __init__(self, parent=None):
        u"""initialize
        :param parent: parent
        :type parent: PySide.QtCore.QObject
        """
        super(EditTableModel, self).__init__(parent)
        self.items = []
        self._input_value = None

    def refresh(self, items):
        u"""情報を更新
        :param items: ファイルパスのリスト
        :type items: list of unicode
        """
        self.layoutAboutToBeChanged.emit()
        self.set_items(items)
        self.modelAboutToBeReset.emit()
        self.modelReset.emit()
        self.layoutChanged.emit()

    def set_items(self, items):
        u"""itemsを更新
        :param items: ファイルパスのリスト
        :type items: list of unicode
        """
        self.items = []
        for _item in items:
            self.items.append(ButtonInfo(_item))

    def headerData(self, col, orientation, role):
        u"""見出しを返す"""
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return ButtonInfo.header[col]
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return col
        return None

    def rowCount(self, parent):
        u"""行数を返す"""
        return len(self.items)

    def columnCount(self, parent):
        u"""カラム数を返す"""
        return ButtonInfo.row_count

    def data(self, index, role):
        u"""カラムのデータを返す"""
        if not index.isValid():
            return None

        item = self.items[index.row()]
        value = item.columns[index.column()].value
        if role == QtCore.Qt.DisplayRole:
            return value

        elif role == QtCore.Qt.TextAlignmentRole:
            return int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        # 背景色を返却
        elif role == QtCore.Qt.BackgroundRole:
            # color = self.__items[index.row()].get("bgcolor", [])
            if isinstance(value, (str, unicode)):
                if value[:1] == '#':
                    return QtGui.QColor(value)
            color = [20, 20, 20]
            return QtGui.QColor(*color)

        elif role == SORT_ROLE:
            return item.widget

        return None

    def flags(self, index):
        return super(EditTableModel, self).flags(index) | QtCore.Qt.ItemIsEditable

    def setData(self, index, value, role=QtCore.Qt.EditRole):

        # 複数入力を行う為に値を一度ストックしておく
        if self._input_value is None:
            # The last selected cell will pass through here to store the value.
            self._input_value = value
        else:
            # All other cells will pass None, so just grab our stored value.
            value = self._input_value

        if role == QtCore.Qt.EditRole:
            item = self.items[index.row()]
            # 型が違うものは入力しない
            if type(item.columns[index.column()].value) != type(value):
                return False

            item.columns[index.column()].value = value
            # item.widget_data_refresh()
            return True
        return False


class Delegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(Delegate, self).__init__(parent)

    '''
    def editorEvent(self, event, model, option, index):
        #print 'editorEvent', event, model, option, index
        super(Delegate, self).editorEvent()
        return True
    '''

    def createEditor(self, parent, option, index):
        # index.column()

        value = index.model().data(index, QtCore.Qt.DisplayRole)
        if isinstance(value, (str, unicode)):
            return QtWidgets.QLineEdit(parent)

        editor = QtWidgets.QSpinBox(parent)
        editor.setMinimum(0)
        editor.setMaximum(9999)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, QtCore.Qt.DisplayRole)
        if isinstance(value, (str, unicode)):
            editor.setText(value)
            return

        editor.setValue(value)

    def setModelData(self, editor, model, index):

        value = index.model().data(index, QtCore.Qt.DisplayRole)
        if isinstance(value, (str, unicode)):
            model.setData(index, editor.text())
            return

        model.setData(index, editor.value())


class EditorTableView(QtWidgets.QTableView):

    def __init__(self, parent=None):
        super(EditorTableView, self).__init__(parent)
        self.model = EditTableModel()
        self.setModel(self.model)
        delegate = Delegate(self.model)
        self.setItemDelegate(delegate)

        if hasattr(self.horizontalHeader(), 'setResizeMode'):
            # PySide
            _d = self.horizontalHeader().setResizeMode
        else:
            # PySide2
            _d = self.horizontalHeader().setSectionResizeMode

        _c = self.horizontalHeader().count()
        for _i in range(_c):
            _d(_i, QtWidgets.QHeaderView.ResizeToContents)


    def closeEditor(self, editor, hint):
        is_cancelled = (hint == QtWidgets.QStyledItemDelegate.RevertModelCache)

        if not is_cancelled:
            for index in self.selectedIndexes():
                if index == self.currentIndex():
                    continue
                # Supply None as the value
                self.model.setData(index, None, QtCore.Qt.EditRole)

        # Reset value for next input
        if self.model._input_value is not None:
            self.model._input_value = None
            self.model.dataChanged.emit(index, index)


        return QtWidgets.QTableWidget.closeEditor(self, editor, hint)

    def set_items(self, items):
        self.model.refresh(items)


class MultiEditorDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super(MultiEditorDialog, self).__init__(parent)
        self.setWindowTitle("MultiEditor")

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)

        self.view = EditorTableView()
        # self.view.setStyleSheet("gridline-color: rgb(191, 191, 191)")
        # self.view.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.selection = self.view.selectionModel()
        self.selection.selectionChanged.connect(self.list_selection_changed)
        self.view.model.dataChanged.connect(self.list_data_changed)


        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.view)

    def list_data_changed(self, topLeft, bottomRight):
        for item in self.view.model.items:
            item.widget_data_refresh()
        self.parent().current_tab_widget_refresh()

    def list_selection_changed(self, selected, deselected):
        '''
        for index in self.view.selectionModel().selectedRows():
            print('Row %d is selected' % index.row())
        '''
        self.parent().reset_selected()
        for index in self.view.selectionModel().selectedIndexes():
            value = index.model().data(index, SORT_ROLE)
            self.parent().selected.append(value)
        #行が選択されていたら列の数だけappendされていたので同じものはまとめとく
        self.parent().selected = list(set(self.parent().selected))
        self.parent().set_stylesheet()
        self.parent().repaint()

    def closeEvent(self, event):
        # 親が保持してる自分を抹殺しておく
        self.parent().multi_edit_view = None

    def sync_list(self):
        buttons = self.parent().get_button_widgets()
        self.view.set_items(buttons)

    # Shelfの選択状況と同期させる
    def parent_select_synchronize(self):
        self.selection.selectionChanged.disconnect()
        _parent_sel = self.parent().selected
        _row_count = self.view.model.rowCount(None)
        rows = []
        for _s in _parent_sel:
            for i in range(_row_count):
                widget = self.view.model.items[i].widget
                if _s == widget:
                    rows.append(i)
                    break

        self.view.selectionModel().clear()
        indexes = [self.view.model.index(r, 0) for r in rows]
        mode = QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows

        [self.view.selectionModel().select(i, mode) for i in indexes]
        self.selection.selectionChanged.connect(self.list_selection_changed)


def main():
    path = lib.get_tab_data_path()
    data = lib.not_escape_json_load(path)
    table_view = MultiEditorDialog(None, data[0]['button'])
    table_view.show()
    sys.exit()
    app.exec_()
#-----------------------------------------------------------------------------
# EOF
#-----------------------------------------------------------------------------
