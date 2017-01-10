slicerMacroBuildScriptedModule(
  NAME DICOMSegmentationPlugin
  SCRIPTS DICOMPluginBase.py DICOMSegmentationPlugin.py
  )

slicerMacroBuildScriptedModule(
  NAME DICOMParametricMapPlugin
  SCRIPTS DICOMPluginBase.py DICOMParametricMapPlugin.py
  )

slicerMacroBuildScriptedModule(
  NAME DICOMTID1500Plugin
  SCRIPTS DICOMPluginBase.py DICOMTID1500Plugin.py
  )

slicerMacroBuildScriptedModule(
  NAME SEGExporterSelfTest
  SCRIPTS SEGExporterSelfTest.py
  )

set(MODULE_PYTHON_RESOURCES
  ../Resources/Icons/icon_unlock.png
  )

slicerMacroBuildScriptedModule(
  NAME QuantitativeReporting
  SCRIPTS QuantitativeReporting.py
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  )
