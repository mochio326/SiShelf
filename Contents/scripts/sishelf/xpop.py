## -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
from . import lib
from . import button


def main():
    _menu = QtWidgets.QMenu()

    path = lib.get_tab_data_path()
    data = lib.not_escape_json_load(path)
    if data is None:
        return

    for _vars in data:
        _m = _menu.addMenu(_vars['name'])

        if _vars.get('button') is not None:
            for _var in _vars['button']:
                # 辞書からインスタンスのプロパティに代入
                data = button.ButtonData()
                for k, v in _var.items():
                    setattr(data, k, v)

                if data.type_ == 0:
                    # 通常ボタン
                    button.normal_data_context(_m, data)
                else:
                    # メニューボタン
                    _m = _m.addMenu(data.label)
                    button.menu_data_context(_m, data.menu_data)

    # マウス位置に出現
    cursor = QtGui.QCursor.pos()

    _menu.setStyleSheet(
        "*{color:#2f2f2f; "
        "background: qlineargradient(x0:0, y1:0, x1:0, y1:1, stop:0 #f2c94c, stop:1 #f2994a); "
        "selection-color: #7e0e18; "
        "selection-background-color: #e27f34; }"
    )

    _menu.exec_(cursor)
