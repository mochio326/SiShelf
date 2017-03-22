## -*- coding: utf-8 -*-
from vendor.Qt import QtCore, QtGui, QtWidgets
import gui.ButtonSetting_ui
reload(gui.ButtonSetting_ui)


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
        #self.drawEOF()
        if self.side.height() == self.height():
            num = 1
        else:
            num = 0
        self.side.setGeometry(0, 0, self.fontMetrics().width("8") * 8, self.height() + num)
        self.drawTab()

    def eventFilter(self, o, e):
        if e.type() == QtCore.QEvent.Paint and o == self.side:
            self.drawLineNumber(o)
            return True
        return False

    def drawEOF(self):
        c = self.textCursor()
        c.movePosition(c.End)
        r = self.cursorRect(c)
        paint = QtGui.QPainter(self.viewport())
        paint.setPen(QtGui.QColor(255, 0, 0))
        paint.setFont(self.currentFont())
        paint.drawText(QtCore.QPoint(r.left(), r.bottom() - 3), "[EOF]")

    def drawTab(self):
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

    def drawLineNumber(self, o):
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

    def __init__(self, *argv, **keywords):
        """init."""
        super(SettingDialog, self).__init__(*argv, **keywords)
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

        self.combo_script_language.addItem("MEL")
        self.combo_script_language.addItem("Python")

    def eventFilter(self,o,e):
        if e.type() == QtCore.QEvent.Paint and o == self.side:
            self.drawLineNumber(o)
            return True
        return False

    def canvas_size(self):
        return self.title.toPlainText()

    @staticmethod
    def get_canvas_size(parent=None):
        u"""ダイアログを開いてキャンバスサイズとOKキャンセルを返す."""
        dialog = SettingDialog(parent)
        result = dialog.exec_()  # ダイアログを開く
        text = dialog.canvas_size()  # キャンバスサイズを取得
        return (text, result == QtWidgets.QDialog.Accepted)


#-----------------------------------------------------------------------------
# EOF
#-----------------------------------------------------------------------------
