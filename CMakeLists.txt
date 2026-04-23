cmake_minimum_required(VERSION 3.16.3...3.19.1 FATAL_ERROR)
project(RadComp)

# Meta-informacion de la extension
set(EXTENSION_HOMEPAGE "https://radcomp.streamlit.app")
set(EXTENSION_CATEGORY "Radiotherapy")
set(EXTENSION_CONTRIBUTORS "Luis Paredes")
set(EXTENSION_DESCRIPTION "A clinical tool for Reirradiation analysis, EQD2 dose calculation, and integrated DVH metrics.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/LuisParedesOcampo/SlicerRadComp/refs/heads/main/Resources/Icons/SlicerRadComp.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/LuisParedesOcampo/SlicerRadComp/refs/heads/main/Resources/Icons/ScreenshotRadComp.png")
set(EXTENSION_DEPENDENCIES SlicerRT)

find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

slicerMacroBuildScriptedModule(
  NAME RadComp
  SCRIPTS
    RadComp.py
  RESOURCES
    Resources/Icons/SlicerRadComp.png
)
