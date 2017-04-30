## -*- coding: utf-8 -*-
from .vendor.Qt import QtWidgets, QtCore
from .gui import shelf_option_ui
from . import lib
import os
import json

class OptionDialog(QtWidgets.QDialog, shelf_option_ui.Ui_Form):
    def __init__(self, parent):
        super(OptionDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Shelf Option")

        # ダイアログのOK/キャンセルボタン
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        self.button_xpop_fontcolor.clicked.connect(self._select_color_font)
        self.button_xpop_bgtopcolor.clicked.connect(self._select_color_bgtop)
        self.button_xpop_bgbottomcolor.clicked.connect(self._select_color_bgbottom)
        self.button_xpop_selectedcolor.clicked.connect(self._select_color_selected)
        self.button_xpop_separator_color.clicked.connect(self._select_color_separator)

        self._data_input()

    def _select_color_font(self):
        color = QtWidgets.QColorDialog.getColor(self.xpop_fontcolor, self)
        if color.isValid():
            self.xpop_fontcolor = color.name()

    def _select_color_bgtop(self):
        color = QtWidgets.QColorDialog.getColor(self.xpop_bgtopcolor, self)
        if color.isValid():
            self.xpop_bgtopcolor = color.name()

    def _select_color_bgbottom(self):
        color = QtWidgets.QColorDialog.getColor(self.xpop_bgbottomcolor, self)
        if color.isValid():
            self.xpop_bgbottomcolor = color.name()

    def _select_color_selected(self):
        color = QtWidgets.QColorDialog.getColor(self.xpop_selectedcolor, self)
        if color.isValid():
            self.xpop_selectedcolor = color.name()

    def _select_color_separator(self):
        color = QtWidgets.QColorDialog.getColor(self.xpop_separator_color, self)
        if color.isValid():
            self.xpop_separator_color = color.name()

    def _data_input(self):
        # データの入力
        data = OptionData()
        self.spinbox_snap_width.setValue(data.snap_width)
        self.spinbox_snap_height.setValue(data.snap_height)
        self.checkbox_snap_active.setChecked(data.snap_active)
        self.checkbox_snap_grid.setChecked(data.snap_grid)
        self.spinbox_tab_height.setValue(data.tab_height)
        self.spinbox_tab_label_size.setValue(data.tab_label_size)

        self.checkbox_xpop_customize.setChecked(data.xpop_customize)
        self.spinbox_xpop_label_size.setValue(data.xpop_label_size)
        self.xpop_fontcolor = data.xpop_fontcolor
        self.xpop_bgtopcolor = data.xpop_bgtopcolor
        self.xpop_bgbottomcolor = data.xpop_bgbottomcolor
        self.xpop_selectedcolor = data.xpop_selectedcolor
        self.spinbox_xpop_separator_height.setValue(data.xpop_separator_height)
        self.xpop_separator_color = data.xpop_separator_color

    def data_save(self):
        data = OptionData()
        data.snap_width = self.spinbox_snap_width.value()
        data.snap_height = self.spinbox_snap_height.value()
        data.snap_active = self.checkbox_snap_active.isChecked()
        data.snap_grid = self.checkbox_snap_grid.isChecked()
        data.tab_height = self.spinbox_tab_height.value()
        data.tab_label_size = self.spinbox_tab_label_size.value()

        data.xpop_customize = self.checkbox_xpop_customize.isChecked()
        data.xpop_label_size = self.spinbox_xpop_label_size.value()
        data.xpop_fontcolor = self.xpop_fontcolor
        data.xpop_bgtopcolor = self.xpop_bgtopcolor
        data.xpop_bgbottomcolor = self.xpop_bgbottomcolor
        data.xpop_selectedcolor = self.xpop_selectedcolor
        data.xpop_separator_height = self.spinbox_xpop_separator_height.value()
        data.xpop_separator_color = self.xpop_separator_color

        data.save()

    @staticmethod
    def open(parent=None):
        '''
        モーダルダイアログを開いてボタン設定とOKキャンセルを返す
        '''
        dialog = OptionDialog(parent)
        result = dialog.exec_()  # ダイアログを開く
        if result == QtWidgets.QDialog.Accepted:
            dialog.data_save()
        data = OptionData()
        return data



class OptionData(object):
    def __init__(self):
        self.snap_active = False
        self.snap_grid = True
        self.snap_width = 20
        self.snap_height = 20
        self.tab_height = 18
        self.tab_label_size = 8
        self.xpop_customize = True
        self.xpop_label_size = 12
        self.xpop_fontcolor = '#2f2f2f'
        self.xpop_bgtopcolor = '#f2c94c'
        self.xpop_bgbottomcolor = '#f2994a'
        self.xpop_selectedcolor = '#e27f34'
        self.xpop_separator_height = 1
        self.xpop_separator_color = '#D2691E'
        self._load()

    def save(self):
        dict_ = {}
        '''
        dict_['snap_active'] = self.snap_active
        dict_['snap_grid'] = self.snap_grid
        dict_['snap_width'] = self.snap_width
        dict_['snap_height'] = self.snap_height
        dict_['tab_height'] = self.tab_height
        dict_['tab_label_size'] = self.tab_label_size
        '''
        dict_ = vars(self)
        lib.make_save_dir()
        f = open(lib.get_shelf_option_filepath(), 'w')
        json.dump(dict_, f)
        f.close()

    def _load(self):
        _path = lib.get_shelf_option_filepath()
        if os.path.isfile(_path) is False:
            return None
        f = open(_path, 'r')
        dict_ = json.load(f)
        for k, v in dict_.items():
            setattr(self, k, v)



#-----------------------------------------------------------------------------
# EOF
#-----------------------------------------------------------------------------
