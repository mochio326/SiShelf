## -*- coding: utf-8 -*-
from vendor.Qt import QtCore, QtGui, QtWidgets


class PartitionWidget(QtWidgets.QWidget):

    def __init__(self, parent):
        self.parent = parent
        super(PartitionWidget, self).__init__(parent)
        self.resize(100, 150)

    def mouseMoveEvent(self, event):
        # 中クリックだけドラッグ＆ドロップ可能にする
        if event.buttons() != QtCore.Qt.MidButton:
            return

        # ドラッグ＆ドロップされるデータ形式を代入
        mimedata = QtCore.QMimeData()

        drag = QtGui.QDrag(self)
        drag.setMimeData(mimedata)
        # ドロップした位置にボタンの左上をセット
        drag.setHotSpot(event.pos() - self.rect().topLeft())
        drop_action = drag.exec_(QtCore.Qt.MoveAction)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        line = QtCore.QLine(QtCore.QPoint(15, 10), QtCore.QPoint(15, 100))
        color = QtGui.QColor(255, 255, 255, 125)
        pen = QtGui.QPen(color, 2)
        painter.setPen(pen)
        painter.drawLine(line)
        painter.save()

        painter.translate(0, 10)
        painter.rotate(90)
        painter.setFont(QtGui.QFont("Arial", 10))
        painter.drawText(QtCore.QPoint(0, 0), u'Partition Line')


#-----------------------------------------------------------------------------
# EOF
#-----------------------------------------------------------------------------
