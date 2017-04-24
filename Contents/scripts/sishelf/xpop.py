## -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
from . import lib
from . import button

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
    )

    _menu.exec_(cursor)


def create_buttons_from_menu(menu_, tab_data):
    if tab_data.get('button') is not None:
        for _var in tab_data['button']:
            # 辞書からインスタンスのプロパティに代入
            data = button.ButtonData()
            for k, v in _var.items():
                setattr(data, k, v)

            if data.type_ == 0:
                # 通常ボタン
                button.normal_data_context(menu_, data)
            else:
                # メニューボタン
                _m = menu_.addMenu(data.label)
                button.menu_data_context(_m, data.menu_data)
