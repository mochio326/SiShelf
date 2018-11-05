## -*- coding: utf-8 -*-
from.vendor.Qt import QtCore, QtGui, QtWidgets

from . import lib


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
        font.setPointSize(self.data.label_font_size_view)
        painter.setFont(font)

        # ウィジェットの大きさを計算　上下左右マージンも考慮
        _w = self.data.line_length
        _h = self.data.margin + int(self.data.line_width * 1.5)
        if self.data.use_label is True:
            fm = painter.fontMetrics()
            if _w < fm.width(self.data.label):
                _w = fm.width(self.data.label)
            if _h < fm.height():
                _h = fm.height()
        _w += self.data.margin * 2
        _h += self.data.margin * 2

        # ラインの配置ポイントを算出
        _line_start_point = self.data.margin
        _line_end_point = self.data.line_length + self.data.margin

        if self.data.style == 0:
            # 水平
            self.resize(_w, _h)
            if self.data.use_label is True:
                _line_height_point = self.data.label_font_size + round(self.data.margin + self.data.line_width / 2)
            else:
                _line_height_point = self.data.margin + round(self.data.line_width / 2)

            line = QtCore.QLine(
                QtCore.QPoint(_line_start_point * self.data.temp_scale, _line_height_point * self.data.temp_scale),
                QtCore.QPoint(_line_end_point * self.data.temp_scale, _line_height_point * self.data.temp_scale)
            )
            painter.drawLine(line)

            if self.data.use_label is True:
                painter.drawText(QtCore.QPoint(0,  self.data.label_font_size), self.data.label)

        elif self.data.style == 1:
            # 垂直
            self.resize(_h, _w)
            line = QtCore.QLine(
                QtCore.QPoint(self.data.margin * self.data.temp_scale, _line_start_point * self.data.temp_scale),
                QtCore.QPoint(self.data.margin * self.data.temp_scale, _line_end_point * self.data.temp_scale)
            )
            painter.drawLine(line)
            if self.data.use_label is True:
                painter.rotate(90)
                _p = QtCore.QPoint(self.data.margin * self.data.temp_scale, (-self.data.margin * 2 - round(self.data.line_width / 2)) * self.data.temp_scale)
                painter.drawText(_p, self.data.label)


class PartitionData(lib.PartsData):
    def __init__(self):
        super(PartitionData, self).__init__()
        self.color = '#aaaaaa'
        self.style = 0  # 0:水平 1:垂直
        self.line_width = 1
        self.line_length = 150
        self.margin = 2


def create(parent, data):
    widget = PartitionWidget(parent, data)
    widget.setObjectName(lib.random_string(15))
    widget.show()
    widget.move(data.position)
    return widget

def update(widget, data):
    font = widget.font()
    font.setPointSize(data.label_font_size)

    widget.move(data.position)


def get_default():
    path = lib.get_partition_default_filepath()
    data = PartitionData()
    js = lib.not_escape_json_load(path)
    if js is not None:
        for k, v in js.items():
            setattr(data, k, v)
    return data

#-----------------------------------------------------------------------------
# EOF
#-----------------------------------------------------------------------------
