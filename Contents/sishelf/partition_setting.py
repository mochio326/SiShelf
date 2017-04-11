## -*- coding: utf-8 -*-
from Qt import QtCore, QtGui, QtWidgets
import gui.partition_setting_ui
import partition


class SettingDialog(QtWidgets.QDialog, gui.partition_setting_ui.Ui_Form):
    def __init__(self, parent, data):
        super(SettingDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Partition Setting")

        # ダイアログのOK/キャンセルボタン
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        self._data_input(data)
        self._preview_partition_drawing()

        # コールバック関数の設定
        func = self._redraw_ui
        self.line_label.textChanged.connect(func)

        self.spinbox_line_length.valueChanged.connect(func)
        self.spinbox_line_width.valueChanged.connect(func)

        self.checkbox_use_label.stateChanged.connect(func)
        self.combo_style.currentIndexChanged.connect(func)
        self.spinbox_label_font_size.valueChanged.connect(func)


        self.button_color.clicked.connect(self._select_color)

    def _redraw_ui(self):
        self._preview_partition_drawing()

    def _select_color(self):
        color = QtWidgets.QColorDialog.getColor(self.color, self)
        if color.isValid():
            self.color = color.name()
            self._preview_partition_drawing()

    def _data_input(self, data):
        # データの入力
        self.line_label.setText(data.label)

        self.spinbox_btn_position_x.setValue(data.position_x)
        self.spinbox_btn_position_y.setValue(data.position_y)

        self.checkbox_use_label.setChecked(data.use_label)
        self.combo_style.setCurrentIndex(data.style)

        self.spinbox_label_font_size.setValue(data.label_font_size)

        self.color = data.color

        self.spinbox_line_length.setValue(data.line_length)
        self.spinbox_line_width.setValue(data.line_width)

    def _preview_partition_drawing(self):
        for child in self.findChildren(partition.PartitionWidget):
            child.setParent(None)
            child.deleteLater()
        parts = partition.create(self, self.get_partition_data_instance())
        parts.position_x = 10
        self.button_preview.addWidget(parts)

    def get_partition_data_instance(self):
        data = partition.PartitionData()
        data.label = self.line_label.text()

        data.position_x = self.spinbox_btn_position_x.value()
        data.position_y = self.spinbox_btn_position_y.value()

        data.use_label = self.checkbox_use_label.isChecked()
        data.style = self.combo_style.currentIndex()

        data.line_length = self.spinbox_line_length.value()
        data.line_width = self.spinbox_line_width.value()

        data.label_font_size = self.spinbox_label_font_size.value()

        data.color = self.color

        return data

    @staticmethod
    def get_data(parent=None, data=None):
        '''
        モーダルダイアログを開いてボタン設定とOKキャンセルを返す
        '''
        dialog = SettingDialog(parent, data)
        result = dialog.exec_()  # ダイアログを開く
        data = dialog.get_partition_data_instance()
        return (data, result == QtWidgets.QDialog.Accepted)



#-----------------------------------------------------------------------------
# EOF
#-----------------------------------------------------------------------------
