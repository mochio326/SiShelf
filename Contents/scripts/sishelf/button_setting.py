## -*- coding: utf-8 -*-
import os
import maya.cmds as cmds
import functools
import copy

from .vendor.Qt import QtCore, QtGui, QtWidgets
from . import button
from . import lib
from .gui import button_setting_ui

class LineNumberTextEdit(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        super(LineNumberTextEdit, self).__init__(parent)
        self.setViewportMargins(self.fontMetrics().width("8") * 8, 0, 0, 0)
        self.side = QtWidgets.QWidget(self)
        self.side.installEventFilter(self)
        self.side.setGeometry(0, 0, self.fontMetrics().width("8") * 8, self.height())
        self.setAcceptDrops(False)
        self.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)

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


class SettingDialog(QtWidgets.QDialog, button_setting_ui.Ui_Form):
    def __init__(self, parent, data):
        super(SettingDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Button Setting")
        # self.setProperty(" saveWindowPref", True)

        self.menulist_widget = None

        # ダイアログのOK/キャンセルボタン
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        #オリジナルの行番号付きLineEditに差し替える
        #designerでのカスタムウィジェットへの差し替えが上手くいかなかったので。
        self.text_script_code = self._replace_widget(
            self.verticalLayout_4,
            self.text_script_code,
            LineNumberTextEdit(self)
        )

        self._data_input(data)
        self._preview_button_drawing()
        self._type_changed()

        self.button_maya_icon.setIcon(QtGui.QIcon(':/mayaIcon.png'))

        # コールバック関数の設定
        func = self._redraw_ui
        self.checkbox_tooltip.stateChanged.connect(func)
        self.line_icon_file.textChanged.connect(func)
        self.checkbox_fix_size.stateChanged.connect(func)
        self.spinbox_width.valueChanged.connect(func)
        self.spinbox_height.valueChanged.connect(func)
        self.checkbox_use_label.stateChanged.connect(func)
        self.checkbox_use_icon.stateChanged.connect(func)
        self.combo_icon_style.currentIndexChanged.connect(func)
        self.spinbox_icon_size.valueChanged.connect(func)
        self.spinbox_label_font_size.valueChanged.connect(func)

        #self.text_script_code.textChanged.connect(func)
        self.combo_script_language.currentIndexChanged.connect(func)

        self.button_maya_icon.clicked.connect(self._get_maya_icon)
        self.button_icon.clicked.connect(self._get_icon)

        self.button_externalfile.clicked.connect(self._get_externalfile)
        self.checkbox_externalfile.stateChanged.connect(func)
        self.line_externalfile.textChanged.connect(func)

        self.checkbox_bgcolor.stateChanged.connect(func)
        self.button_bgcolor.clicked.connect(self._select_bgcolor)

        self.checkbox_label_color.stateChanged.connect(func)
        self.button_label_color.clicked.connect(self._select_label_color)

        self.combo_type.currentIndexChanged.connect(self._type_changed)

        # テキストエリアに日本語を入力中（IME未確定状態）にMayaがクラッシュする場合があった。
        # textChanged.connect をやめ、例えば focusOut や エンターキー押下を発火条件にすることで対応
        # self.text_label.textChanged.connect(func)
        # self.text_tooltip.textChanged.connect(func)

        def _focus_out(event):
            self._redraw_ui()

        def _key_press(event, widget=None):
            QtWidgets.QTextEdit.keyPressEvent(widget, event)

            key = event.key()
            if (key == QtCore.Qt.Key_Enter) or (key == QtCore.Qt.Key_Return):
                self._redraw_ui()

        self.text_label.focusOutEvent = _focus_out
        self.text_tooltip.focusOutEvent = _focus_out
        self.text_label.keyPressEvent = functools.partial(_key_press, widget=self.text_label)
        self.text_tooltip.keyPressEvent = functools.partial(_key_press, widget=self.text_tooltip)
        self.text_label.setToolTip('It will be reflected in the preview when focus is out.')
        self.text_tooltip.setToolTip('It will be reflected in the preview when focus is out.')

        self.text_script_code.focusOutEvent = _focus_out
        self.text_script_code.keyPressEvent = functools.partial(_key_press, widget=self.text_script_code)


    def _type_changed(self):
        _parent = self.menulist_layout
        _idx = self.combo_type.currentIndex()
        _widget = self.menulist_widget
        if _idx == 0:
            if _widget is not None:
                _parent.removeWidget(_widget)
                _widget.setVisible(False)
                _widget.setParent(None)
                _widget.deleteLater()
        else:
            _ls = []
            for _tmp in self.menu_data:
                _ls.append(_tmp['label'])

            self.menulist_model = QtCore.QStringListModel()
            self.menulist_model.setStringList(_ls)
            self.menulist_widget = QtWidgets.QListView()
            self.menulist_widget.setModel(self.menulist_model)
            self.menulist_widget.resize(70, self.menulist_widget.height())
            self.menulist_widget.setMaximumSize(QtCore.QSize(200, 16777215))
            _parent.addWidget(self.menulist_widget)
            self.menulist_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            self.menulist_widget.customContextMenuRequested.connect(self._menulist_context)
            menulist_sel_model = self.menulist_widget.selectionModel()
            menulist_sel_model.selectionChanged.connect(self._menulist_changed)
            self.menulist_widget.setCurrentIndex(self.menulist_model.index(0))

            self.dele = ListDelegate()
            self.dele.changeValue.connect(self._menulist_change_value)
            self.menulist_widget.setItemDelegate(self.dele)

        self._apply_script_commands_data()

    def _menulist_change_value(self, idx, value):
        self.menu_data[idx]['label'] = value

    def _menulist_changed(self, current, previous):
        # _i = current.row()
        self._apply_script_commands_data()

    def _menulist_context(self):
        _menu = QtWidgets.QMenu(self)
        _menu.addAction('Add', self._menulist_add)
        _menu.addAction('Delete', self._menulist_delete)
        cursor = QtGui.QCursor.pos()
        _menu.exec_(cursor)

    def _menulist_add(self):
        _dict = button.make_menu_button_dict()
        _dict['label'] = 'menu button' + str(len(self.menu_data))
        self.menu_data.append(_dict)
        _ls = []
        for _tmp in self.menu_data:
            _ls.append(_tmp['label'])
        self.menulist_model.setStringList(_ls)

    def _menulist_delete(self):
        _index = self.menulist_widget.currentIndex()
        self.menulist_model.removeRow(_index.row())
        del self.menu_data[_index.row()]

    def _keep_script_commands_data(self):
        _idx = self.combo_type.currentIndex()
        # ノーマルボタン
        if _idx == 0:
            _d = self.normal_data
        else:
            _list_idx = self.menulist_widget.currentIndex()
            _d = self.menu_data[_list_idx.row()]

        _d['use_externalfile'] = self.checkbox_externalfile.isChecked()
        _d['externalfile'] = self.line_externalfile.text()
        _d['script_language'] = self.combo_script_language.currentText()
        _d['code'] = self.text_script_code.toPlainText()

    def _apply_script_commands_data(self):
        _idx = self.combo_type.currentIndex()
        # ノーマルボタン
        if _idx == 0:
            _d = self.normal_data
        else:
            _list_idx = self.menulist_widget.currentIndex()
            if len(self.menu_data) == 0:
                self._menulist_add()
            _d = self.menu_data[_list_idx.row()]

        self.text_script_code.setPlainText(_d['code'])
        self.line_externalfile.setText(_d['externalfile'])
        index = self.combo_script_language.findText(_d['script_language'])
        self.combo_script_language.setCurrentIndex(index)
        # checkbox_externalfileを最後に適用しないとline_externalfileが正常に反映されなかった。
        self.checkbox_externalfile.setChecked(_d['use_externalfile'])


    def _redraw_ui(self):
        #外部ファイルを指定されている場合は言語を強制変更
        if self.checkbox_externalfile.isChecked() is True:
            _path = self.line_externalfile.text()
            _suffix = QtCore.QFileInfo(_path).completeSuffix()
            if _suffix == "py":
                script_language = 'Python'
            else:
                script_language = 'MEL'
            index = self.combo_script_language.findText(script_language)
            self.combo_script_language.setCurrentIndex(index)

        self._preview_button_drawing()
        self._keep_script_commands_data()
        self.repaint()

        self.text_script_code.setReadOnly(self.checkbox_externalfile.isChecked())

    def _select_bgcolor(self):
        color = QtWidgets.QColorDialog.getColor(self.bgcolor, self)
        if color.isValid():
            self.bgcolor = color.name()
            self._preview_button_drawing()

    def _select_label_color(self):
        color = QtWidgets.QColorDialog.getColor(self.label_color, self)
        if color.isValid():
            self.label_color = color.name()
            self._preview_button_drawing()

    def _data_input(self, data):
        # データの入力
        self.text_label.setPlainText(data.label)
        self.text_tooltip.setPlainText(data.tooltip)
        self.checkbox_tooltip.setChecked(data.bool_tooltip)

        self.line_icon_file.setText(data.icon_file)
        self.spinbox_btn_position_x.setValue(data.position_x)
        self.spinbox_btn_position_y.setValue(data.position_y)

        self.checkbox_fix_size.setChecked(data.size_flag)
        self.spinbox_width.setValue(data.width)
        self.spinbox_height.setValue(data.height)

        self.checkbox_use_label.setChecked(data.use_label)
        self.checkbox_use_icon.setChecked(data.use_icon)
        self.combo_icon_style.setCurrentIndex(data.icon_style)

        self.spinbox_icon_size.setValue(data.icon_size_x)

        self.spinbox_label_font_size.setValue(data.label_font_size)

        self.checkbox_bgcolor.setChecked(data.use_bgcolor)
        self.bgcolor = data.bgcolor

        self.checkbox_label_color.setChecked(data.use_label_color)
        self.label_color = data.label_color

        #self.text_script_code.setPlainText(data.code)
        #self.checkbox_externalfile.setChecked(data.use_externalfile)
        #self.line_externalfile.setText(data.externalfile)
        #index = self.combo_script_language.findText(data.script_language)
        #self.combo_script_language.setCurrentIndex(index)

        self.combo_type.setCurrentIndex(data.type_)
        self.menu_data = copy.deepcopy(data.menu_data)

        # ノーマルボタン用のデータを保持
        _dict = button.make_menu_button_dict()
        _dict['code'] = data.code
        _dict['use_externalfile'] = data.use_externalfile
        _dict['externalfile'] = data.externalfile
        _dict['script_language'] = data.script_language
        self.normal_data = _dict

    def _replace_widget(self, parent, old_widget, new_widget):
        parent.removeWidget(old_widget)
        old_widget.setVisible(False)
        old_widget.setParent(None)
        old_widget.deleteLater()
        parent.addWidget(new_widget)
        return new_widget

    def _preview_button_drawing(self):
        for child in self.findChildren(button.ButtonWidget):
            child.setParent(None)
            child.deleteLater()
        btn = button.create(self, self.get_button_data_instance(), True)

        # センタリング用のspacerを仕込むとmayaが落ちるようになったのでひとまず封印
        # spacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        #self.button_preview.addItem(spacer)
        self.button_preview.addWidget(btn)
        #self.button_preview.addItem(spacer)

        self.set_stylesheet()
        self.repaint()

    def set_stylesheet(self):
        css = ''
        buttons = self.findChildren(button.ButtonWidget)
        css = lib.button_css(buttons, css)
        self.setStyleSheet(css)

    def _get_maya_icon(self):
        icon, result = DccIconViewer.get_icon_name(self)
        if result:
            self.line_icon_file.setText(icon)

    def _get_icon(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', os.path.expanduser('~') + '/Desktop')
        self.line_icon_file.setText(filename[0])

    def _get_externalfile(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', os.path.expanduser('~') + '/Desktop')
        path = filename[0]
        self.line_externalfile.setText(path)

    def get_button_data_instance(self):
        data = button.ButtonData()
        data.label = self.text_label.toPlainText()

        data.bool_tooltip = self.checkbox_tooltip.isChecked()
        data.tooltip = self.text_tooltip.toPlainText()

        data.icon_file = self.line_icon_file.text()
        data.position_x = self.spinbox_btn_position_x.value()
        data.position_y = self.spinbox_btn_position_y.value()

        data.size_flag = self.checkbox_fix_size.isChecked()
        data.width = self.spinbox_width.value()
        data.height = self.spinbox_height.value()

        data.use_label = self.checkbox_use_label.isChecked()
        data.use_icon = self.checkbox_use_icon.isChecked()
        data.icon_style = self.combo_icon_style.currentIndex()

        data.icon_size_x = self.spinbox_icon_size.value()
        data.icon_size_y = self.spinbox_icon_size.value()

        data.label_font_size = self.spinbox_label_font_size.value()

        data.use_bgcolor = self.checkbox_bgcolor.isChecked()
        data.bgcolor = self.bgcolor

        data.use_label_color = self.checkbox_label_color.isChecked()
        data.label_color = self.label_color

        # data.use_externalfile = self.checkbox_externalfile.isChecked()
        # data.externalfile = self.line_externalfile.text()
        # data.script_language = self.combo_script_language.currentText()
        # data.code = self.text_script_code.toPlainText()

        data.use_externalfile = self.normal_data['use_externalfile']
        data.externalfile =self.normal_data['externalfile']
        data.script_language = self.normal_data['script_language']
        data.code = self.normal_data['code']

        data.type_ = self.combo_type.currentIndex()
        data.menu_data = copy.deepcopy(self.menu_data)

        return data

    @staticmethod
    def get_data(parent=None, data=None):
        '''
        モーダルダイアログを開いてボタン設定とOKキャンセルを返す
        '''
        dialog = SettingDialog(parent, data)
        result = dialog.exec_()  # ダイアログを開く
        data = dialog.get_button_data_instance()
        dialog.normal_data = None
        return (data, result == QtWidgets.QDialog.Accepted)


class ListDelegate(QtWidgets.QItemDelegate):
    changeValue = QtCore.Signal(int, str)

    def createEditor(self, parent, option, index):
        # 編集する時に呼ばれるWidgetを設定
        editor = QtWidgets.QLineEdit(parent)
        return editor

    def setEditorData(self, LineEdit, index):
        # 編集されたときに呼ばれ、セットされた値をWidgetにセットする?
        value = index.model().data(index, QtCore.Qt.EditRole)
        LineEdit.setText(value)

    def setModelData(self, LineEdit, model, index):
        # ModelにSpinboxの編集した値をセットする?

        value = LineEdit.text()
        # 編集情報をSignalで発信する
        self.changeValue.emit(index.row(), value)
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)




class DccIconViewer(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(DccIconViewer, self).__init__(parent)
        self.view = QtWidgets.QListView()
        self.view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        # ダイアログのOK/キャンセルボタンを用意
        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.view)
        layout.addWidget(btns)

        self.model = QtGui.QStandardItemModel()
        self.view.setIconSize(QtCore.QSize(32, 32))
        self.view.setModel(self.model)
        self.set_item()

        self.view.setAlternatingRowColors(True)
        self.resize(300, 500)

    def set_item(self):
        images = get_icon_list()
        for img in images:
            item = QtGui.QStandardItem(img)
            item.setIcon(QtGui.QIcon(':/{0}'.format(img)))
            self.model.appendRow(item)

    def icon_name(self):
        select_model = self.view.selectionModel()
        if select_model.hasSelection() is False:
            return ''
        for index in select_model.selectedIndexes():
            file_path = self.model.data(index)
        return ':/' + file_path

    @staticmethod
    def get_icon_name(parent=None):
        dialog = DccIconViewer(parent)
        result = dialog.exec_()  # ダイアログを開く
        name = dialog.icon_name()  # キャンバスサイズを取得
        return (name, result == QtWidgets.QDialog.Accepted)

# #################################################################################################
# Maya依存の部分
# #################################################################################################
def get_icon_list():
    return cmds.resourceManager(nameFilter='*.*')

#-----------------------------------------------------------------------------
# EOF
#-----------------------------------------------------------------------------
