## -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
from . import lib
from . import button
import copy

TITLE = 'SiShelfXPOP'


def main(tab=None, load_file=None):
    '''

    :param tab: タブ名を文字列で指定。
    　　　　　　 通常第１階層がタブになるが、タブ名を指定すればタブの内部が第１階層になる
    :return:
    '''

    # 同名のウインドウが存在したら削除
    # 1～2回は消えてくれるけど、その後は残ってしまうバグあり。
    # 方法が違うのかもしれない…
    ui = lib.get_ui(TITLE, 'QMenu')
    if ui is not None:
        ui.close()
        ui.setParent(None)
        ui.deleteLater()

    _menu = QtWidgets.QMenu()
    _menu.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
    _menu.setObjectName(TITLE)

    if load_file is None:
        path = lib.get_tab_data_path()
    else:
        path = load_file

    save_data = lib.not_escape_json_load(path)
    if save_data is None:
        return

    if tab is None:
        # タブ名を第１階層にする
        for _vars in save_data:
            _m = _menu.addMenu(_vars['name'])
            if _vars['reference'] is not None:
                _w = QtWidgets.QWidget()
                icon = QtGui.QIcon(_w.style().standardIcon(QtWidgets.QStyle.SP_ArrowDown))
                _m.setIcon(icon)
                _data = lib.not_escape_json_load(_vars['reference'])
                create_buttons_from_menu(_m, _data)
            else:
                create_buttons_from_menu(_m, _vars)
    else:
        for _vars in save_data:
            if _vars['name'] == tab:
                create_buttons_from_menu(_menu, _vars)

    # マウス位置に出現
    cursor = QtGui.QCursor.pos()

    _menu.setStyleSheet(
        "*{color:#2f2f2f; "
        "background: qlineargradient(x0:0, y1:0, x1:0, y1:1, stop:0 #f2c94c, stop:1 #f2994a); "
        "selection-color: #7e0e18; "
        "selection-background-color: #e27f34; }"
       "QMenu::separator {"
        "height:1px; background:chocolate; margin-left:1px; margin-right:3px;"
        "}"
    )

    _menu.exec_(cursor)


def create_buttons_from_menu(menu_, tab_data):
    if tab_data.get('button') is not None:
        for _var in tab_data['button']:
            # 辞書からインスタンスのプロパティに代入
            data = button.ButtonData()
            for k, v in _var.items():
                setattr(data, k, v)

            if data.xpop_visibility is False:
                continue

            if data.xpop_spacer is True:
                menu_.addSeparator()

            if data.type_ == 0:
                # 通常ボタン
                button.normal_data_context(menu_, data)
            else:
                # メニューボタン
                _m = menu_.addMenu(data.label)
                button.menu_data_context(_m, data.menu_data)


class XpopSettingDialog(QtWidgets.QDialog):

    def __init__(self, parent=None, parts=None):
        '''
        :param parent:
        :param parts: XPOPで扱うパーツ（ボタン）のリスト
        '''
        super(XpopSettingDialog, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setWindowTitle('XPOP Setting')
        self._parts = copy.deepcopy(parts)
        self.view = QtWidgets.QTreeView()
        self.view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.view.setAlternatingRowColors(True)

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

        self.model = QtGui.QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Label', 'Visibility', 'InsertSpacer'])
        self.view.setIconSize(QtCore.QSize(32, 32))
        self.view.setModel(self.model)

        if hasattr(self.view.header(), 'setResizeMode'):
            # PySide
            self.view.header().setResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
            self.view.header().setResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
            self.view.header().setResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        else:
            # PySide2
            self.view.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
            self.view.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
            self.view.header().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.set_item()
        self.view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self._context)
        self.view.setAlternatingRowColors(True)
        self.resize(400, 500)


    def _context(self):
        _menu = QtWidgets.QMenu(self)
        _menu.addAction('Up', self._up)
        _menu.addAction('Down', self._down)
        cursor = QtGui.QCursor.pos()
        _menu.exec_(cursor)

    def _up(self):
        self._get_check_data()
        _index = self.view.currentIndex()
        if _index.row() == 0 or _index is QtCore.QModelIndex():
            return
        _i = _index.row()
        self._parts[_i - 1], self._parts[_i] = self._parts[_i], self._parts[_i - 1]
        self.set_item()
        _sel = self.model.createIndex(_i - 1, 0)
        self.view.setCurrentIndex(_sel)

    def _down(self):
        self._get_check_data()
        _index = self.view.currentIndex()
        if _index.row() == len(self._parts)-1 or _index is QtCore.QModelIndex():
            return
        _i = _index.row()
        self._parts[_i + 1], self._parts[_i] = self._parts[_i], self._parts[_i + 1]
        self.set_item()
        _sel = self.model.createIndex(_i + 1, 0)
        self.view.setCurrentIndex(_sel)

    def set_item(self):
        index = 0
        for _p in self._parts:
            _label = QtGui.QStandardItem(_p.label)
            if _p.use_icon:
                _label.setIcon(_p.icon)

            _vis = QtGui.QStandardItem()
            _vis.setCheckable(True)
            if _p.xpop_visibility:
                _vis.setCheckState(QtCore.Qt.Checked)
            else:
                _vis.setCheckState(QtCore.Qt.Unchecked)

            _spa = QtGui.QStandardItem()
            _spa.setCheckable(True)
            if _p.xpop_spacer:
                _spa.setCheckState(QtCore.Qt.Checked)
            else:
                _spa.setCheckState(QtCore.Qt.Unchecked)

            self.model.setItem(index, 0, _label)
            self.model.setItem(index, 1, _vis)
            self.model.setItem(index, 2, _spa)

            index += 1

    def _get_check_data(self):
        for i in range(self.model.rowCount()):
            self._parts[i].xpop_visibility = (self.model.item(i, 1).checkState() == QtCore.Qt.Checked)
            self._parts[i].xpop_spacer = (self.model.item(i, 2).checkState() == QtCore.Qt.Checked)
        return self._parts


    @staticmethod
    def show_dialog(parent=None, parts=None):
        dialog = XpopSettingDialog(parent, parts)
        result = dialog.exec_()  # ダイアログを開く
        parts = dialog._get_check_data()
        return parts, result == QtWidgets.QDialog.Accepted