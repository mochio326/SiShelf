## -*- coding: utf-8 -*-
from vendor.Qt import QtCore, QtGui, QtWidgets
import gui.ButtonSetting_ui
reload(gui.ButtonSetting_ui)
import ShelfButton

class LineNumberTextEdit(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        super(LineNumberTextEdit, self).__init__(parent)
        self.setViewportMargins(self.fontMetrics().width("8") * 8, 0, 0, 0)
        self.side = QtWidgets.QWidget(self)
        self.side.installEventFilter(self)
        self.side.setGeometry(0, 0, self.fontMetrics().width("8") * 8, self.height())
        self.setAcceptDrops(False)

    def paintEvent(self, e):
        super(LineNumberTextEdit, self).paintEvent(e)
        #self.draw_eof()
        if self.side.height() == self.height():
            num = 1
        else:
            num = 0
        self.side.setGeometry(0, 0, self.fontMetrics().width("8") * 8, self.height() + num)
        self.draw_tab()

    def eventFilter(self, o, e):
        if e.type() == QtCore.QEvent.Paint and o == self.side:
            self.draw_line_number(o)
            return True
        return False

    def draw_eof(self):
        c = self.textCursor()
        c.movePosition(c.End)
        r = self.cursorRect(c)
        paint = QtGui.QPainter(self.viewport())
        paint.setPen(QtGui.QColor(255, 0, 0))
        paint.setFont(self.currentFont())
        paint.drawText(QtCore.QPoint(r.left(), r.bottom() - 3), "[EOF]")

    def draw_tab(self):
        tabchar = "›"
        c = self.cursorForPosition(QtCore.QPoint(0, 0))
        paint = QtGui.QPainter()
        paint.begin(self.viewport())
        paint.setPen(QtGui.QColor(150, 150, 150))
        paint.setFont(self.currentFont())
        c = self.document().find("	", c)
        while not c.isNull():
            c.movePosition(QtGui.QTextCursor.Left)
            r = self.cursorRect(c)
            if r.bottom() > self.height() + 10: break
            paint.drawText(QtCore.QPoint(r.left(), r.bottom() - 3), tabchar)
            c.movePosition(QtGui.QTextCursor.Right)
            c = self.document().find("	", c)
        paint.end()

    def draw_line_number(self, o):
        c = self.cursorForPosition(QtCore.QPoint(0, 0))
        block = c.block()
        paint = QtGui.QPainter()
        paint.begin(o)
        paint.setPen(QtGui.QColor(150, 150, 150))
        paint.setFont(self.currentFont())
        while block.isValid():
            c.setPosition(block.position())
            r = self.cursorRect(c)
            if r.bottom() > self.height() + 10: break
            paint.drawText(QtCore.QPoint(10, r.bottom() - 3), str(block.blockNumber() + 1))
            block = block.next()
        paint.end()

class SettingDialog(QtWidgets.QDialog, gui.ButtonSetting_ui.Ui_Form):
    def __init__(self, parent, btn_data):
        super(SettingDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Button Setting")

        # ダイアログのOK/キャンセルボタン
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        #オリジナルの行番号付きLineEcitに差し替える
        #designerでのカスタムウィジェットへの差し替えが上手くいかなかったので。
        self.verticalLayout_4.removeWidget(self.text_script_code)
        self.text_script_code.setVisible(False)
        self.text_script_code.deleteLater()
        self.text_script_code = LineNumberTextEdit(self)
        self.verticalLayout_4.addWidget(self.text_script_code)

        # データの入力
        self.text_label.setPlainText(btn_data.label)
        self.text_script_code.setPlainText(btn_data.code)
        self.line_icon_file.setText(btn_data.icon_file)
        self.spinbox_btn_position_x.setValue(btn_data.position_x)
        self.spinbox_btn_position_y.setValue(btn_data.position_y)

        self.checkbox_fix_size.setChecked(btn_data.fix_size_flag)
        self.spinbox_btn_size_x.setValue(btn_data.btn_size_x)
        self.spinbox_btn_size_y.setValue(btn_data.btn_size_y)

        self.checkbox_use_label.setChecked(btn_data.use_label)
        self.checkbox_use_icon.setChecked(btn_data.use_icon)
        self.combo_icon_style.setCurrentIndex(btn_data.icon_style)

        self.spinbox_icon_size_x.setValue(btn_data.icon_size_x)
        self.spinbox_icon_size_y.setValue(btn_data.icon_size_y)

    def eventFilter(self,o,e):
        if e.type() == QtCore.QEvent.Paint and o == self.side:
            self.draw_line_number(o)
            return True
        return False

    def get_button_data_instance(self):
        data = ShelfButton.ButtonData()
        data.label = self.text_label.toPlainText()
        data.code = self.text_script_code.toPlainText()
        data.icon_file = self.line_icon_file.text()
        data.position_x = self.spinbox_btn_position_x.value()
        data.position_y = self.spinbox_btn_position_y.value()

        data.fix_size_flag = self.checkbox_fix_size.isChecked()
        data.btn_size_x = self.spinbox_btn_size_x.value()
        data.btn_size_y = self.spinbox_btn_size_y.value()

        data.use_label = self.checkbox_use_label.isChecked()
        data.use_icon = self.checkbox_use_icon.isChecked()
        data.icon_style = self.combo_icon_style.currentIndex()

        data.icon_size_x = self.spinbox_icon_size_x.value()
        data.icon_size_y = self.spinbox_icon_size_y.value()

        return data

    @staticmethod
    def get_data(parent=None, data=None):
        '''
        モーダルダイアログを開いてボタン設定とOKキャンセルを返す
        '''
        dialog = SettingDialog(parent, data)
        result = dialog.exec_()  # ダイアログを開く
        data = dialog.get_button_data_instance()
        return (data, result == QtWidgets.QDialog.Accepted)


#-----------------------------------------------------------------------------
# EOF
#-----------------------------------------------------------------------------
