# RadReirradiation 🧬

### Radiotherapy Re-irradiation Analysis and Biological Dose Summation in 3D Slicer

**RadReirradiation** utilizes the **Linear-Quadratic (LQ)** model to perform voxel-by-voxel calculations of Biologically Effective Dose (BED) and EQD2 (Equivalent Dose in 2 Gy fractions), enabling precise evaluation of the accumulated dose in critical structures and tumor volumes (DVH).

<img width="1919" height="701" alt="image" src="https://github.com/user-attachments/assets/8ca2476f-8099-419e-a42c-a3b2d6cb43af" />

## Features 🚀
* **Interactive Manual Pre-Alignment:** Introduced a brand-new, safe manual pre-alignment panel. Users can now translate the Moving CT using intuitive sliders before running the automatic registration.
* **Smart "Auto-Center" for CBCTs:** Added a one-click "Auto-Center CTs" button. It calculates the true RAS mathematical center of both datasets (bypassing FOV discrepancies common in Linac CBCTs) and teleports the images to match, automatically jumping all 2D slice views to the new target.
* **Image Registration Wrapper:** Automated Rigid, Affine and Deformable (B-Spline) registration workflows using the BRAINSFit engine, eliminating the need to switch between multiple Slicer modules.
* **Auto-Resampling Dose Engine:** Automatically resamples the moving dose grid to perfectly match the reference geometry, preventing matrix dimension errors during biological accumulation.
* **Smart UI Automation:** The module intelligently auto-selects the aligned volumes for the biological calculation step, reducing human error.
* **Time-Corrected Radiobiology:** Full support for standard LQ model (BED and EQD2) with temporal recovery factors for accurate reirradiation assessment.
* **Voxel-by-Voxel processing:** Operates directly on DICOM RTDOSE arrays using NumPy for high-performance biological conversion.
* **Simultaneous Integrated Boost (SIB) support:** Automatically respects varying dose-per-fraction gradients within the same volume.
* **Time-Based Recovery Factor:** Applies partial biological recovery discounts to the base plan based on the interval between treatments.
* **"Eclipse-Style" Dose Wash:** Custom dynamic color map transition (Dark Blue to Red) with a 2 Gy threshold and 40% opacity, replicating the familiar visual experience of commercial Treatment Planning Systems (TPS).
* **Seamless SlicerRT Integration:** Output volumes are directly compatible with SlicerRT's Dose Volume Histogram (DVH) module.
* **Dosimetric Analysis:** Metrics table (Dmax, Dmean) synchronized with structure visibility.
*  **DVH Generation:** Generation of interactive DVH curves within the Slicer.

## 📚 Scientific Foundation and References
The development of RadReirradiation is based on international standards for reporting and accumulating biological doses.

### Reference Publication (RadReirradiation)
* **Status:** In Preparation. 
* *Note:* Once the specific scientific article for this tool is published, this section will be updated with a direct link to PubMed/the corresponding Journal.

### Background Literature and Consensus
This module formally implements the concepts discussed in the following key publications:
1. **ReCOG Consensus (2024):** *Reirradiation Collaborative Group (ReCOG) consensus on
standards for dose evaluation and reporting in patients with
multiple courses of radiation therapy:*. [https://pubmed.ncbi.nlm.nih.gov/41643699/]
2. **Nieder et al. (2017/2018):** Second re-irradiation: a narrative review of the available clinical data. [https://pubmed.ncbi.nlm.nih.gov/29187033/]
3. **Nieder et al. (2017/2018):** Repeat reirradiation of the spinal cord: multi-national expert treatment
recommendations*. [https://doi.org/10.1007/s00066-018-1266-6]

## Installation 🛠️
1. Download or clone this repository to your local machine.
2. Open 3D Slicer.
3. In 3D Slicer, go to **Developer Tools** -> **Extension Wizard**.
4. Click **Select Extension** and choose the folder where you downloaded this code..
5. Restart 3D Slicer. The module will now appear under the **Radiotherapy** category.
6. **Recommended Dependency:** It is highly recommended to have **SlicerRT** installed for the seamless importation and handling of DICOM-RT objects.

## Step-by-step tutorial 🛠️
To perform an accurate re-irradiation analysis, you must export two complete datasets from your Treatment Planning System (TPS): the Previous (1) Treatment and the Current/Planned Treatment (2).

<img width="679" height="266" alt="0" src="https://github.com/user-attachments/assets/4493ec9f-dac8-485c-b845-ac161f34d67d" />

Export Requirements (from your TPS):
* CT Images (CT)
* RT Doses (RD)
* RT Structure Sets (RS)
* Optional but recommended: RT Plans (RP)

<img width="1182" height="581" alt="1" src="https://github.com/user-attachments/assets/4051c8e3-1dba-4cd6-8d44-8b48f292e470" />

Succesfull exportation of the previous treatmet, repeat the same steps for the current/planned treatmet

<img width="1187" height="577" alt="2" src="https://github.com/user-attachments/assets/5abe9de0-c1a2-48b4-91ba-bd2f509485d8" />

**Importing into 3D Slicer:**

Ensure you have the SlicerRT extension installed. It is a mandatory requirement to read and process Radiotherapy DICOM files. Drag and drop your exported DICOM folders into the 3D Slicer application or use the native DICOM Browser.
Crucial Step: When the DICOM import window appears, ensure the "eye" icon next to your RT Structures is toggled ON (visible). If this icon is closed, the structures will not be loaded into the scene and cannot be evaluated.

<img width="1202" height="772" alt="3" src="https://github.com/user-attachments/assets/c8e57085-13bf-4b7d-af89-d7e2dae9fa4e" />


Data Organization Tip:
Since TPS exports often generate generic names, it is highly recommended to open the Data module in Slicer and rename your loaded volumes immediately (e.g., rename them to CT_Previous, CT_Current, Dose_Previous, Dose_Current). This will prevent confusion when assigning volumes in the RadReirradiation module.







## Disclaimer ⚠️
**This software is for research and educational purposes only and has not been cleared for clinical use by any regulatory body (FDA, CE, etc.).**
The user assumes all responsibility for the interpretation and clinical application of the results provided by this tool. Calculations must be independently verified by a certified Medical Physicist or Radiation Oncologist before any clinical decision.

**Autor:** Luis Paredes, Clinical Medical Physicist (Cali, Colombia).
**Web version:** [radcomp.streamlit.app](https://radcomp.streamlit.app)
