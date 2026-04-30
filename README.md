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

**1. Data Preparation: From TPS to 3D Slicer**

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

Ensure you have the SlicerRT extension installed. It is a mandatory requirement to read and process Radiotherapy DICOM files. Drag and drop your exported DICOM folders into the 3D Slicer application or use the native DICOM Browser and click on Examine button.

<img width="1202" height="772" alt="3" src="https://github.com/user-attachments/assets/c8e57085-13bf-4b7d-af89-d7e2dae9fa4e" />
<img width="1916" height="995" alt="4" src="https://github.com/user-attachments/assets/79303f7a-ca0d-4811-878f-30696658eed1" />
Once the DICOM files are loaded only check the TAC, RD and RS of the previous and current treatmets, click on Load button. RP is optional; it is not used in this version but will be used in future developments.  
<img width="1380" height="245" alt="5" src="https://github.com/user-attachments/assets/0d384dfb-b3c6-46e5-8363-484765c64c5d" />
Crucial Steps: When the DICOM import window appears, ensure the "eye" icon next to your RT Structures is toggled ON (visible). If this icon is closed, the structures will not be loaded into the scene and the DVH cannot be evaluated.

Data Organization Tip:
Since TPS exports often generate generic names (In this example, the RTDOSE files in both treatmets have the same name), it is highly recommended to rename your loaded volumes immediately (e.g., rename them to CT_Previous, CT_Current, Dose_Previous, Dose_Current). This will prevent confusion when assigning volumes in the RadReirradiation module.
<img width="1881" height="984" alt="6" src="https://github.com/user-attachments/assets/fe9bea1a-5ed5-43a5-8bde-c243d972ddac" />
<img width="1130" height="285" alt="7" src="https://github.com/user-attachments/assets/58de03d2-7cf9-46bb-9243-8ed392857d68" />


**2. Loading Data and Smart Alignment**

Once your DICOM data is properly imported and organized in 3D Slicer, it is time to load it into the extension to coregister the previous treatment with the current patient anatomy.

Launching the Module:

* Open the module dropdown menu (usually displaying "Welcome to Slicer").
* Navigate to Radiotherapy and select RadReirradiation.

<img width="1170" height="981" alt="8" src="https://github.com/user-attachments/assets/d06ce3f6-5496-48ed-8806-f3d7d5e557d9" />


**RadReirradiation**  has 4 important modules, which are:

1. Data selection and image registration with Dose resample.
2. Structures visualization (important for the DVH analysis).
3. Reirradiation calculation settings.
4. Metrics an DVH results.
     
<img width="1221" height="907" alt="10" src="https://github.com/user-attachments/assets/66350799-ce81-48d3-8620-94167a546602" />


**Assigning Volumes:**

In the Data Selection panel, carefully assign your loaded volumes to their corresponding roles:
* Moving CT / Previous CT: The historical anatomy that needs to be registered.
* RTDOSE Previous treatment.
* Fixed CT / Current /planned CT: The anatomy where the final dose summation will be evaluated.
* RTDOSE Current/planned Treatment.

<img width="523" height="249" alt="9" src="https://github.com/user-attachments/assets/3bc186c4-953e-4961-8806-9d16133841b0" />

**Pre-Alignment and Image Registration with Dose resample:**

Before computing any biological dose, both CTs must be spatially aligned. Click the "Auto-Center CTs" button. This will automatically match the mathematical centers of both image sets, providing an excellent starting point.
At this point, it is recommended to hide the structures to better visualize the Pre-Aligment and image Registration results. To do this, use module 2 (Structures visualization), select the RS CURRENT file, and press the "Hide all structures" button.

<img width="1920" height="1007" alt="11" src="https://github.com/user-attachments/assets/a1a32f96-e860-47de-9c8b-e2b062f028e5" />

Use the manual sliders to fine-tune the alignment if the patient setups were significantly different, this will be the starting point for the image registration and Dose resample algorithm.

<img width="1770" height="890" alt="12" src="https://github.com/user-attachments/assets/d36b17ae-6067-4cf9-8669-29d6164cf2a7" />

 **Registration Options & Processing Time:**

 Press the button Auto-Registration and Dose resample, this uses the built-in BRAINSFit integration to lock the previous CT and its dose onto the current anatomy. the module includes two checkeable options for improve image registration results:
 
* Affine Registration: Performs a linear transformation (translation, rotation, scaling, and shearing).
* Deformable Registration: Performs a non-linear transformation (BSpline) that adapts to anatomical changes between the two scans, such as weight loss or tumor shrinkage.
* ⚠️ Warning: Please note that checking those options, especially the Deformable option, is computationally intensive. It may take several minutes to complete depending on your computer's hardware specifications.

**Visualizing the Fusion Results:**

After the registration is complete, it is highly recommended to perform a visual Quality Assurance (QA). Use Slicer's native foreground/background fade sliders (located at the top of the 2D slice views) to blend the Previous CT and Current CT. This visual check ensures the accuracy of the alignment before proceeding to the dose calculation.

<img width="1846" height="889" alt="13" src="https://github.com/user-attachments/assets/15ca65fe-f9af-4316-ae5f-793881cdfea1" />










## Disclaimer ⚠️
**This software is for research and educational purposes only and has not been cleared for clinical use by any regulatory body (FDA, CE, etc.).**
The user assumes all responsibility for the interpretation and clinical application of the results provided by this tool. Calculations must be independently verified by a certified Medical Physicist or Radiation Oncologist before any clinical decision.

**Autor:** Luis Paredes, Clinical Medical Physicist (Cali, Colombia).
**Web version:** [radcomp.streamlit.app](https://radcomp.streamlit.app)
