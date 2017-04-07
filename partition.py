## -*- coding: utf-8 -*-
from vendor.Qt import QtCore, QtGui, QtWidgets
import lib


class PartitionWidget(QtWidgets.QWidget):

    def __init__(self, parent, data):
        self.parent = parent
        self.data = data
        super(PartitionWidget, self).__init__(parent)

    def mouseMoveEvent(self, event):
        # 中クリックだけドラッグ＆ドロップ可能にする
        if event.buttons() != QtCore.Qt.MidButton:
            return
        # ドラッグ＆ドロップされるデータ形式を代入
        mimedata = QtCore.QMimeData()
        drag = QtGui.QDrag(self)
        drag.setMimeData(mimedata)
        drag.exec_(QtCore.Qt.MoveAction)

    def paintEvent(self, event):
        # スタイルシートを利用
        super(PartitionWidget, self).paintEvent(event)
        opt = QtWidgets.QStyleOption()
        opt.initFrom(self)
        p = QtGui.QPainter(self)
        s = self.style()
        s.drawPrimitive(QtWidgets.QStyle.PE_Widget, opt, p, self)

        # ラベルとラインの描画
        painter = QtGui.QPainter(self)

        color = QtGui.QColor(self.data.color)
        pen = QtGui.QPen(color, self.data.line_width)
        painter.setPen(pen)

        font = QtGui.QFont()
        font.setPointSize(self.data.label_font_size)
        painter.setFont(font)

        # ウィジェットの大きさを計算　上下左右マージンも考慮
        _w = self.data.line_length
        _h = self.data.margin + self.data.line_width
        if self.data.use_label is True:
            fm = painter.fontMetrics()
            if _w < fm.width(self.data.label):
                _w = fm.width(self.data.label)
            if _h < fm.height():
                _h = fm.height()
        _w += self.data.margin * 2
        _h += self.data.margin * 2

        if self.data.type == 0:
            # 水平
            self.resize(_w, _h)
            line = QtCore.QLine(
                QtCore.QPoint(0, self.data.label_font_size + self.data.margin),
                QtCore.QPoint(self.data.line_length, self.data.label_font_size + self.data.margin)
            )
            painter.drawLine(line)
            if self.data.use_label is True:
                painter.drawText(QtCore.QPoint(0,  self.data.label_font_size), self.data.label)

        elif self.data.type == 1:
            # 垂直
            self.resize(_h, _w)
            line = QtCore.QLine(
                QtCore.QPoint(self.data.margin, self.data.margin),
                QtCore.QPoint(self.data.margin, self.data.line_length + self.data.margin)
            )
            painter.drawLine(line)
            if self.data.use_label is True:
                painter.rotate(90)
                painter.drawText(QtCore.QPoint(self.data.margin, -self.data.margin*2), self.data.label)






class PartitionData(lib.PartsData):
    def __init__(self):
        super(PartitionData, self).__init__()

        self.color = '#aaaaaa'
        self.type = 1  # 0:水平 1:垂直
        self.line_width = 1
        self.line_length = 150
        self.margin = 2

        #test
        self.label = 'label test'
        self.label_font_size = 10
        self.use_label = True


def create(parent, data):
    widget = PartitionWidget(parent, data)
    widget.setObjectName(lib.random_string(15))
    #widget.show()
    widget.move(data.position)
    return widget

#-----------------------------------------------------------------------------
# EOF
#-----------------------------------------------------------------------------
