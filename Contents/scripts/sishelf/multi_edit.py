## -*- coding: utf-8 -*-
from.vendor.Qt import QtCore, QtGui, QtWidgets

from . import lib
import sys

# from __future__ import absolute_import, division, print_function

class Column(object):
    u"""カラム情報"""

    def __init__(self, index, value):
        self.index = index
        self.value = value


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


class FileInfo(Columns):
    u"""ファイル情報"""
    header = ['label', 'x', 'y', 'width', 'height']
    row_count = len(header)

    def __init__(self, dict):
        u"""initialize
        :param path: ファイルパス
        :type path: unicode
        """
        super(FileInfo, self).__init__()
        self.label = Column(0, dict.get('label'))
        self.x = Column(1, dict.get('position_x'))
        self.y = Column(2, dict.get('position_y'))
        self.width = Column(3, dict.get('width'))
        self.height = Column(4, dict.get('height'))


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
            self.items.append(FileInfo(_item))

    def headerData(self, col, orientation, role):
        u"""見出しを返す"""
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return FileInfo.header[col]
        return None

    def rowCount(self, parent):
        u"""行数を返す"""
        return len(self.items)

    def columnCount(self, parent):
        u"""カラム数を返す"""
        return FileInfo.row_count

    def data(self, index, role):
        u"""カラムのデータを返す"""
        if not index.isValid():
            return None

        item = self.items[index.row()]
        if role == QtCore.Qt.DisplayRole:
            return item.columns[index.column()].value
        elif role == QtCore.Qt.TextAlignmentRole:
            return int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        # 背景色を返却
        elif role == QtCore.Qt.BackgroundRole:
            # color = self.__items[index.row()].get("bgcolor", [])
            color = [20, 20, 20]
            return QtGui.QColor(*color)

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

        return QtWidgets.QTableWidget.closeEditor(self, editor, hint)


    def set_items(self, items):
        self.model.refresh(items)



class MultiEditorDialog(QtWidgets.QDialog):
    def __init__(self, parent, data):
        super(MultiEditorDialog, self).__init__(parent)
        self.setWindowTitle("MultiEditor")

        self.view = EditorTableView()
        self.view.set_items(data)


        # ダイアログのOK/キャンセルボタンを用意
        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.view)
        layout.addWidget(btns)



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
