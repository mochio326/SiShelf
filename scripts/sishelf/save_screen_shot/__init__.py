from . import util
from . import cropImage

from maya import OpenMayaUI
from maya import OpenMaya

import os


def _saveBuffer(savePath, tmpImgExtension="bmp"):
    img = OpenMaya.MImage()
    view = OpenMayaUI.M3dView.active3dView()
    view.readColorBuffer(img, True)
    img.writeToFile(savePath, tmpImgExtension)


def SaveScreenShot(outPath, tmpImgExtension="bmp"):
    util.CheckDirectory(outPath)
    tmp_file = util.GetTempImgPath(extension=tmpImgExtension)

    _saveBuffer(tmp_file)

    result = cropImage.CropImage.RunCropImage(tmp_file, outPath, parent=GetMayaMainWindow())

    os.remove(tmp_file)

    return (result is 1)


def GetMayaMainWindow():
    from ..vendor import Qt
    from ..vendor.Qt import QtWidgets

    if Qt.IsPySide2:
        import shiboken2 as shiboken
    else:
        import shiboken

    return shiboken.wrapInstance(long(OpenMayaUI.MQtUtil_mainWindow()), QtWidgets.QMainWindow)
