import os
import qt
import ctk
import vtk
import slicer
import inspect

import vtkSegmentationCorePython as vtkSegmentationCore

from QRUtils.testdata import TestDataLogic

from slicer.ScriptedLoadableModule import ScriptedLoadableModuleTest, ScriptedLoadableModuleWidget

__all__ = ['QuantitativeReportingTest']


class QuantitativeReportingTests:

  def __init__(self, parent):
    parent.title = "Quantitative Reporting Tests"
    parent.categories = ["Testing.TestCases"]
    parent.dependencies = ["QuantitativeReporting"]
    parent.contributors = ["Christian Herz (SPL, BWH), Andrey Fedorov (SPL, BWH)"]
    parent.helpText = """
    This self test includes creation/read of a structured report (DICOM TID1500) including its segmentation.
    For more information: <a>https://github.com/QIICR/QuantitativeReporting</a>
    """
    parent.acknowledgementText = """
    This work was supported in part by the National Cancer Institute funding to the
    Quantitative Image Informatics for Cancer Research (QIICR) (U24 CA180918).
    """
    self.parent = parent

    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['QuantitativeReporting'] = self.runTest
    slicer.selfTests['QuantitativeReportingTests'] = self.runTest

  def runTest(self):
    tester = QuantitativeReportingTest()
    tester.runTest()


class QuantitativeReportingTestsWidget(ScriptedLoadableModuleWidget):

  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self, parent)

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    self.testsCollapsibleButton = ctk.ctkCollapsibleButton()
    self.testsCollapsibleButton.setLayout(qt.QFormLayout())
    self.testsCollapsibleButton.text = "Quantitative Reporting Tests"
    self.layout.addWidget(self.testsCollapsibleButton)
    self.generateButtons()

  def generateButtons(self):

    def onButtonPressed(button):
      print "pressed button %s" % button.name
      tester = QuantitativeReportingTest()
      tester.setUp()
      getattr(tester, button.name)()

    buttons = []
    for testName in [f for f in QuantitativeReportingTest.__dict__.keys() if f.startswith('test_')]:
      b = qt.QPushButton(testName)
      b.name = testName
      self.testsCollapsibleButton.layout().addWidget(b)
      buttons.append(b)

    map(lambda b: b.clicked.connect(lambda clicked: onButtonPressed(b)), buttons)


class QuantitativeReportingTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  collection = "CTLiver"

  data = {
    "volume": {
      "uid": "1.2.392.200103.20080913.113635.1.2009.6.22.21.43.10.23430.1"
    },
    "seg_dcm": {
      "uid": "1.2.276.0.7230010.3.1.3.0.68336.1510953324.321969"
    },
    "sr": {
      "uid": "1.2.276.0.7230010.3.1.3.0.68337.1510953324.625906"
    }
  }

  @property
  def layoutManager(self):
    return slicer.app.layoutManager()

  def setUp(self):
    self.delayDisplay("Closing the scene")
    slicer.mrmlScene.Clear(0)
    self.setupTimer()

  def setupTimer(self):
    self.timer = qt.QTimer()
    self.timer.setInterval(1000)
    self.timer.setSingleShot(True)
    self.timer.timeout.connect(self._selectModule)
    self.timer.start()

  def loadTestVolume(self):
    self.delayDisplay("Loading testdata")

    qrWidget = slicer.modules.QuantitativeReportingWidget
    qrWidget.loadTestData(self.collection, imageDataType="volume", uid=self.data["volume"]["uid"])

  def runTest(self):
    """Run as few or as many tests as needed here.
    """

    for testName in [f for f in QuantitativeReportingTest.__dict__.keys() if f.startswith('test_')]:
      self.setUp()
      getattr(self, testName)()

  def test_read_report(self):

    self.delayDisplay('Starting %s' % inspect.stack()[0][3])

    def loadTestData():
      for imageType, fileData in self.data.iteritems():
        if not len(slicer.dicomDatabase.filesForSeries(fileData['uid'])):
          sampleData = TestDataLogic.downloadAndUnzipSampleData(self.collection)
          TestDataLogic.importIntoDICOMDatabase(sampleData[imageType])

    def checkFocusAndClickButton():
      focus = slicer.app.focusWidget()
      focus.parent().parent().yesButton.click()

    loadTestData()

    dicomWidget = slicer.modules.dicom.widgetRepresentation().self()
    checkbox = dicomWidget.detailsPopup.pluginSelector.checkBoxByPlugin["DICOMLongitudinalTID1500Plugin"]
    crntState = checkbox.checked
    checkbox.checked = False

    timer = qt.QTimer()
    timer.setInterval(3000)
    timer.setSingleShot(True)
    timer.timeout.connect(checkFocusAndClickButton)
    timer.start()

    qrWidget = slicer.modules.QuantitativeReportingWidget
    qrWidget.loadSeries(self.data['sr']['uid'])

    checkbox.checked = crntState

    tableNodes = slicer.util.getNodesByClass("vtkMRMLTableNode")

    self.assertTrue(len(tableNodes),
                    "Loading SR into mrmlScene failed. No vtkMRMLTableNodes were found within the scene.")

    self.delayDisplay('Selecting measurements report')

    qrWidget.measurementReportSelector.setCurrentNode(tableNodes[0])

    self.delayDisplay('Checking number of segments')
    self.assertTrue(len(qrWidget.segmentEditorWidget.segments) == 3,
                    "Number of segments does not match expected count of 3")

    self.delayDisplay('Checking referenced master volume', 2000)
    self.assertIsNotNone(qrWidget.segmentEditorWidget.masterVolumeNode,
                         "Master volume for the selected measurement report is None!")

    self.delayDisplay('Test passed!')

  def test_create_report(self):

    self.delayDisplay('Starting %s' % inspect.stack()[0][3])

    qrWidget = slicer.modules.QuantitativeReportingWidget

    self.loadTestVolume()
    success, err = qrWidget.saveReport()
    self.assertFalse(success)

    self.delayDisplay('Add segments')

    qrWidget = slicer.modules.QuantitativeReportingWidget
    segmentation = qrWidget.segmentEditorWidget.segmentationNode.GetSegmentation()

    segmentGeometries = {
      'Tumor': [[2, 30, 30, -127.7], [2, 40, 40, -127.7], [2, 50, 50, -127.7], [2, 40, 80, -127.7]],
      'Air': [[2, 60, 100, -127.7], [2, 80, 30, -127.7]]
    }

    for segmentName, segmentGeometry in segmentGeometries.iteritems():
      appender = vtk.vtkAppendPolyData()

      for sphere in segmentGeometry:
        sphereSource = vtk.vtkSphereSource()
        sphereSource.SetRadius(sphere[0])
        sphereSource.SetCenter(sphere[1], sphere[2], sphere[3])
        appender.AddInputConnection(sphereSource.GetOutputPort())

      segment = vtkSegmentationCore.vtkSegment()
      segment.SetName(segmentation.GenerateUniqueSegmentID(segmentName))

      appender.Update()
      representationName = vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationClosedSurfaceRepresentationName()
      segment.AddRepresentation(representationName, appender.GetOutput())
      segmentation.AddSegment(segment)

    self.delayDisplay('Save report')

    success, err = qrWidget.saveReport()
    self.assertTrue(success)

    self.delayDisplay('Test passed!')

  def test_import_labelmap(self):

    self.delayDisplay('Starting %s' % inspect.stack()[0][3])

    qrWidget = slicer.modules.QuantitativeReportingWidget
    self.loadTestVolume()

    sampleData = TestDataLogic.downloadAndUnzipSampleData(self.collection)
    segmentationsDir = sampleData['seg_nrrd']

    labels = []
    for f in [os.path.join(segmentationsDir, f) for f in os.listdir(segmentationsDir) if f.endswith(".nrrd")]:
      _, label = slicer.util.loadVolume(f, {'labelmap': True}, returnNode=True)
      if label:
        labels.append(label)

    labelImportWidget = qrWidget.labelMapImportWidget

    timer = qt.QTimer()
    timer.setInterval(2000)
    timer.timeout.connect(self._checkFocusAndClickButton)
    timer.start()

    for label in labels:
      labelImportWidget.labelMapSelector.setCurrentNode(label)
      labelImportWidget.importButton.click()

    timer.stop()

    segmentation = qrWidget.segmentEditorWidget.segmentationNode.GetSegmentation()
    self.assertEquals(segmentation.GetNumberOfSegments(), len(labels))

    self.delayDisplay('Test passed!')

  def _checkFocusAndClickButton(self):
    focus = slicer.app.focusWidget()
    if type(focus) is qt.QPushButton:
      focus.click()

  def test_import_segmentation(self):

    self.delayDisplay('Starting %s' % inspect.stack()[0][3])

    uid = self.data["seg_dcm"]["uid"]

    self.loadTestVolume()

    if not len(slicer.dicomDatabase.filesForSeries(uid)):
      sampleData = TestDataLogic.downloadAndUnzipSampleData(self.collection)
      TestDataLogic.importIntoDICOMDatabase(sampleData["seg_dcm"])

    def checkFocusAndClickButton():
      focus = slicer.app.focusWidget()
      focus.parent().parent().noButton.click()

    timer = qt.QTimer()
    timer.setInterval(3000)
    timer.setSingleShot(True)
    timer.timeout.connect(checkFocusAndClickButton)
    timer.start()

    qrWidget = slicer.modules.QuantitativeReportingWidget
    qrWidget.loadSeries(uid)

    segmentationNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[-1]

    qrWidget.importSegmentationCollapsibleButton.collapsed = False

    importWidget = qrWidget.segmentImportWidget
    importWidget.otherSegmentationNodeSelector.setCurrentNode(segmentationNode)

    segmentIDs = qrWidget.segmentEditorWidget.logic.getSegmentIDs(segmentationNode, False)
    importWidget.otherSegmentsTableView.setSelectedSegmentIDs(segmentIDs)

    importWidget.copyOtherToCurrentButton.click()

    self.delayDisplay('Checking number of imported segments')
    self.assertTrue(len(qrWidget.segmentEditorWidget.segments) == 3,
                    "Number of segments does not match expected count of 3")

    self.delayDisplay('Test passed!')

  def _selectModule(self):
    self.layoutManager.selectModule("QuantitativeReporting")