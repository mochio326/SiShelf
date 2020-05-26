from ..vendor.Qt import QtWidgets, QtGui, QtCore
import os


class CropImage(QtWidgets.QDialog):
    def __init__(self, imgPath="", outPath="", parent=None):
        super(CropImage, self).__init__(parent=parent)
        self.__image = None
        self.__img_path = None
        self.__out_path = None
        self.__rect_start = QtCore.QPoint(0, 0)
        self.__rect_end = QtCore.QPoint(0, 0)
        self.__draw_rect = False
        self.__show_desc = True

        self.__qt_trns_color = QtGui.QColor(0, 0, 0, 125)
        self.__qt_rect_pen = QtGui.QPen(QtCore.Qt.gray)
        self.__qt_rect_pen.setStyle(QtCore.Qt.DashLine)
        self.__qt_rect_pen.setWidth(3)
        self.__qt_white_pen = QtGui.QPen(QtCore.Qt.white)
        self.__qt_font = QtGui.QFont("Arial", 16)

        self.setImage(imgPath)
        self.setOutPath(outPath)

    @staticmethod
    def RunCropImage(imgPath, outPath, parent=None):
        dial = CropImage(imgPath, outPath, parent=parent)
        return dial.exec_()

    def setOutPath(self, path):
        self.__out_path = path

    def setImage(self, path):
        self.__img_path = path
        self.__image = QtGui.QImage(self.__img_path)

        self.__resetWidget()

    def __resetWidget(self):
        size = self.__image.size()
        if size.width() < 1 or size.height() < 1:
            size = QtCore.QSize(10, 10)

        self.setFixedSize(size)

    def __saveImage(self):
        if self.__out_path:
            if self.__draw_rect:
                cropped = self.__image.copy(*self.__getDrawRectTuple())
                cropped.save(self.__out_path)
            else:
                self.__image.save(self.__out_path)

    def __getDrawRectTuple(self):
        i_size = self.__image.size()
        iw = i_size.width()
        ih = i_size.height()

        if self.__rect_start.x() <= self.__rect_end.x():
            x1 = self.__rect_start.x()
            x2 = self.__rect_end.x()
        else:
            x1 = self.__rect_end.x()
            x2 = self.__rect_start.x()

        if self.__rect_start.y() <= self.__rect_end.y():
            y1 = self.__rect_start.y()
            y2 = self.__rect_end.y()
        else:
            y1 = self.__rect_end.y()
            y2 = self.__rect_start.y()
        
        rx = x1 if x1 >= 0 else 0
        rw = (x2 if x2 <= iw else iw) - rx
        ry = y1 if y1 >= 0 else 0
        rh = (y2 if y2 <= ih else ih) - ry

        return (rx, ry, rw, rh)

    def keyPressEvent(self, event):
        key = event.key()

        if key == QtCore.Qt.Key_Escape:
            self.reject()

        elif key == QtCore.Qt.Key_Return or key == QtCore.Qt.Key_Enter:
            self.__saveImage()
            self.accept()

    def mousePressEvent(self, event):
        if event.button() is QtCore.Qt.LeftButton:
            self.__draw_rect = True
            self.__show_desc = False
            self.__rect_start = event.pos()
            self.__rect_end = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() is QtCore.Qt.LeftButton:
            self.__rect_end = event.pos()
            if (self.__rect_end - self.__rect_start).manhattanLength() < 10:
                self.__draw_rect = False

            self.update()

    def mouseMoveEvent(self, event):
        self.__rect_end = event.pos()
        self.update()

    def paintEvent(self, event):
        super(CropImage, self).paintEvent(event)

        if self.__image is not None:
            p = QtGui.QPainter(self)

            i_size = self.__image.size()
            p.drawImage(QtCore.QRect(0, 0, i_size.width(), i_size.height()), self.__image)
            iw = i_size.width()
            ih = i_size.height()

            if self.__show_desc:
                p.setPen(self.__qt_rect_pen)
                p.setFont(self.__qt_font)
                p.fillRect(0, 0, iw, ih, self.__qt_trns_color)
                p.drawRect(iw * 0.1, ih * 0.1, iw * 0.8, ih * 0.8)
                p.setPen(self.__qt_white_pen)
                p.drawText(QtCore.QRect(0, 0, iw, ih), QtCore.Qt.AlignCenter, "Select Capture Area\nPress Enter to save\nPress Escape to cancel")

            elif self.__draw_rect:
                p.setPen(self.__qt_rect_pen)
                
                rx, ry, rw, rh = self.__getDrawRectTuple()
                dx = rx + rw
                dy = ry + rh
                if rx > 1:
                    p.fillRect(0, 0, rx, ih, self.__qt_trns_color)
                if dx < (iw - 1):
                    p.fillRect(dx, 0, iw, ih, self.__qt_trns_color)
                if ry > 1:
                    p.fillRect(rx, 0, rw, ry - 1, self.__qt_trns_color)
                if dy < (ih - 1):
                    p.fillRect(rx, dy, rw, ih, self.__qt_trns_color)

                p.drawRect(QtCore.QRect(rx, ry, rw, rh))
