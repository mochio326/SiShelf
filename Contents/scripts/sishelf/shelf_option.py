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

        self._data_input()

    def _data_input(self):
        # データの入力
        data = OptionData()
        self.spinbox_snap_width.setValue(data.snap_width)
        self.spinbox_snap_height.setValue(data.snap_height)
        self.checkbox_snap_active.setChecked(data.snap_active)
        self.checkbox_snap_grid.setChecked(data.snap_grid)

    def data_save(self):
        data = OptionData()
        data.snap_width = self.spinbox_snap_width.value()
        data.snap_height = self.spinbox_snap_height.value()
        data.snap_active = self.checkbox_snap_active.isChecked()
        data.snap_grid = self.checkbox_snap_grid.isChecked()
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
        self._load()

    def save(self):
        dict_ = {}
        dict_['snap_active'] = self.snap_active
        dict_['snap_grid'] = self.snap_grid
        dict_['snap_width'] = self.snap_width
        dict_['snap_height'] = self.snap_height

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
