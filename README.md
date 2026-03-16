# SlicerRadComp 🧬

A clinical tool for 3D Slicer that calculates biologically effective dose (BED) and equivalent dose in 2 Gy fractions (EQD2) for radiotherapy plan accumulation and reirradiation analysis. 

This module performs voxel-by-voxel mathematical operations to biologically sum multiple radiation courses, applying time-based recovery factors, and returns a fully integrated EQD2 volume for clinical analysis (DVH).

Companion web application: [RadComp on Streamlit](https://radcomp.streamlit.app)

## Features 🚀
* **Fast Image Registration Wrapper:** Automated Rigid and Deformable (B-Spline) registration workflows using the BRAINSFit engine, eliminating the need to switch between multiple Slicer modules.
* **Auto-Resampling Engine:** Automatically resamples the moving dose grid to perfectly match the reference geometry, preventing matrix dimension errors during biological accumulation.
* **Smart UI Automation:** The module intelligently auto-selects the aligned volumes for the biological calculation step, reducing human error.
* **Time-Corrected Radiobiology:** Full support for standard LQ model (BED and EQD2) with temporal recovery factors for accurate reirradiation assessment.
* **Voxel-by-Voxel processing:** Operates directly on DICOM RTDOSE arrays using NumPy for high-performance biological conversion.
* **Simultaneous Integrated Boost (SIB) support:** Automatically respects varying dose-per-fraction gradients within the same volume.
* **Time-Based Recovery Factor:** Applies partial biological recovery discounts to the base plan based on the interval between treatments.
* **"Eclipse-Style"** Dose Wash: Custom dynamic color map transition (Dark Blue to Red) with a 2 Gy threshold and 40% opacity, replicating the familiar visual experience of commercial Treatment Planning Systems (TPS).
* **Seamless SlicerRT Integration:** Output volumes are directly compatible with SlicerRT's Dose Volume Histogram (DVH) module.
* **Dosimetric Analysis:** Metrics table (Dmax, Dmean) synchronized with structure visibility.
*  **DVH Generation:** Generation of interactive DVH curves within the Slicer.

## Installation 🛠️
1. Download or clone this repository to your local machine.
2. Open 3D Slicer.
3. In 3D Slicer, go to **Developer Tools** -> **Extension Wizard**.
4. Click **Select Extension** and choose the folder where you downloaded this code..
5. Restart 3D Slicer. The module will now appear under the **Radiotherapy** category.

## Disclaimer ⚠️
**This software is for research and educational purposes only and has not been cleared for clinical use by any regulatory body (FDA, CE, etc.).**
The user assumes all responsibility for the interpretation and clinical application of the results provided by this tool. Calculations must be independently verified by a certified Medical Physicist or Radiation Oncologist before any clinical decision.

**Autor:** Luis Paredes, Clinical Medical Physicist (Cali, Colombia).
**Web version:** [radcomp.streamlit.app](https://radcomp.streamlit.app)
