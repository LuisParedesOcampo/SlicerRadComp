import logging
import os
import vtk
import ctk
import qt
import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin


# ==========================================================
# 1. METADATOS DEL MÓDULO
# ==========================================================
class RadReirradiation(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "RadReirradiation: Radiotherapy Reirradiation Analysis"
        self.parent.categories = ["Radiotherapy"]
        self.parent.dependencies = []
        self.parent.contributors = [
            "Luis Paredes, Clinical Medical Physicist (Cali, Colombia) www.linkedin.com/in/lfparedes1"]
        self.parent.helpText = """
        This module allows for re-irradiation analysis through EQD2 dose calculation, study alignment, and integrated dosimetric metrics.
        Visit: https://RadComp.streamlit.app .
        """
        self.parent.acknowledgementText = "Developed for the Medical Physics community."


# ==========================================================
# 2. INTERFAZ GRÁFICA (WIDGET / GUI)
# ==========================================================
class RadReirradiationWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)
        self.logic = None

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        self.logic = RadReirradiationLogic()

        # ==========================================
        # PANEL 1: FAST IMAGE REGISTRATION
        # ==========================================
        registrationCollapsibleButton = ctk.ctkCollapsibleButton()
        registrationCollapsibleButton.text = "Image Registration and Dose Resample "
        registrationCollapsibleButton.collapsed = False  # Que inicie abierto
        self.layout.addWidget(registrationCollapsibleButton)
        registrationFormLayout = qt.QFormLayout(registrationCollapsibleButton)

        # Selector: CT RT1 Tratamiento Móvil (Antiguo)
        self.moving_ct_selector = slicer.qMRMLNodeComboBox()
        self.moving_ct_selector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        #  self.moving_ct_selector.addAttribute("vtkMRMLScalarVolumeNode", "DICOM.Modality", "CT")
        self.moving_ct_selector.setMRMLScene(slicer.mrmlScene)
        self.moving_ct_selector.setToolTip("CT from the previous treatment RT1 (Moving).")
        registrationFormLayout.addRow("CT from previous treatment RT1 (Moving): ", self.moving_ct_selector)

        # Selector: Dosis Antigua (A remuestrear)
        self.moving_dose_selector = slicer.qMRMLNodeComboBox()
        self.moving_dose_selector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        #  self.moving_dose_selector.addAttribute("vtkMRMLScalarVolumeNode", "DICOM.Modality", "RTDOSE")
        self.moving_dose_selector.showChildNodeTypes = True  # Vital para ver RTDOSE
        self.moving_dose_selector.setMRMLScene(slicer.mrmlScene)
        self.moving_dose_selector.setToolTip(
            "The Dose (RD) from the previous treatment RT1 that you want to align to the new grid.")
        registrationFormLayout.addRow("RTDOSE previous treatment RT1 (Moving): ", self.moving_dose_selector)

        # Selector: CT RT2 tratamiento Fijo (Nuevo)
        self.fixed_ct_selector = slicer.qMRMLNodeComboBox()
        self.fixed_ct_selector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        #  self.fixed_ct_selector.addAttribute("vtkMRMLScalarVolumeNode", "DICOM.Modality", "CT")
        self.fixed_ct_selector.setMRMLScene(slicer.mrmlScene)
        self.fixed_ct_selector.setToolTip("CT from the planned treatment RT2 (Fixed).")
        registrationFormLayout.addRow("CT from planned treatment RT2 (Fixed): ", self.fixed_ct_selector)

        # Selector: Dosis Nueva (Para usar su cuadrícula como molde)
        self.fixed_dose_selector = slicer.qMRMLNodeComboBox()
        self.fixed_dose_selector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        #  self.fixed_dose_selector.addAttribute("vtkMRMLScalarVolumeNode", "DICOM.Modality", "RTDOSE")
        self.fixed_dose_selector.showChildNodeTypes = True
        self.fixed_dose_selector.setMRMLScene(slicer.mrmlScene)
        self.fixed_dose_selector.setToolTip(
            "The Dosage of the NEW plan. Its geometric matrix will be used as a template.")
        registrationFormLayout.addRow("RTDOSE planned treatment RT2 (Fixed): ", self.fixed_dose_selector)

        # --- NUEVO: Panel Seguro de Pre-Alineación Manual ---
        self.preAlignCollapsibleButton = ctk.ctkCollapsibleButton()
        self.preAlignCollapsibleButton.text = "1. Manual Pre-Alignment (Translate)"
        registrationFormLayout.addRow(self.preAlignCollapsibleButton)
        preAlignLayout = qt.QFormLayout(self.preAlignCollapsibleButton)

        # Botón de teletransporte
        self.centerButton = qt.QPushButton("Auto-Center CTs")
        self.centerButton.toolTip = "Teleports the Moving CT to the Fixed CT center before manual adjustment."
        self.centerButton.setStyleSheet("background-color: #0078D7; color: white; font-weight: bold; padding: 5px;")
        preAlignLayout.addRow(self.centerButton)

        # Sliders (barras deslizadoras)
        self.sliderX = ctk.ctkSliderWidget()
        self.sliderX.minimum, self.sliderX.maximum, self.sliderX.value = -300, 300, 0
        self.sliderX.suffix = " mm"
        self.sliderX.enabled = False
        preAlignLayout.addRow("Right/Left (X):", self.sliderX)

        self.sliderY = ctk.ctkSliderWidget()
        self.sliderY.minimum, self.sliderY.maximum, self.sliderY.value = -300, 300, 0
        self.sliderY.suffix = " mm"
        self.sliderY.enabled = False
        preAlignLayout.addRow("Ant/Post (Y):", self.sliderY)

        self.sliderZ = ctk.ctkSliderWidget()
        self.sliderZ.minimum, self.sliderZ.maximum, self.sliderZ.value = -400, 400, 0
        self.sliderZ.suffix = " mm"
        self.sliderZ.enabled = False
        preAlignLayout.addRow("Sup/Inf (Z):", self.sliderZ)

        # Variables de control
        self.manual_transform_node = None
        self.base_translation = [0.0, 0.0, 0.0]

        # Conectar los botones y barras a las funciones
        self.centerButton.connect('clicked(bool)', self.onCenterButtonClicked)
        self.sliderX.connect('valueChanged(double)', self.onSliderValueChanged)
        self.sliderY.connect('valueChanged(double)', self.onSliderValueChanged)
        self.sliderZ.connect('valueChanged(double)', self.onSliderValueChanged)

        # Casilla para Registro Afín (Escala y Cizalladura)
        self.affine_checkbox = qt.QCheckBox("Enable Affine Transform (Slower, high RAM)")
        self.affine_checkbox.setChecked(False)
        self.affine_checkbox.setToolTip(
            "It adds 12 degrees of freedom. Ideal for skull or calibration differences between CTs, but it requires a lot of RAM.")
        registrationFormLayout.addRow(self.affine_checkbox)

        # Casilla para Registro Deformable
        self.deformable_checkbox = qt.QCheckBox(
            "Enable Deformable (B-Spline) Registration, It will take several minutes..")
        self.deformable_checkbox.setChecked(False)
        self.deformable_checkbox.setToolTip(
            "First calculate Rigid, then apply Deformable. This may take several minutes.")
        registrationFormLayout.addRow(self.deformable_checkbox)

        # Botón Azul de Registro
        self.registerButton = qt.QPushButton("Auto-Registration and Dose Resample")
        self.registerButton.toolTip = "It performs an automatic hard registration and adjusts the dose grid.."
        self.registerButton.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        registrationFormLayout.addRow(self.registerButton)

        # Connect Register button to function
        self.registerButton.connect('clicked(bool)', self.onRegisterButton)

        # ==========================================================
        # PANEL 2: ESTRUCTURAS Y VISUALIZACIÓN
        # ==========================================================
        structuresCollapsibleButton = ctk.ctkCollapsibleButton()
        structuresCollapsibleButton.text = "2: Structures & Visualization"
        self.layout.addWidget(structuresCollapsibleButton)
        structuresFormLayout = qt.QFormLayout(structuresCollapsibleButton)

        # 1. Selector del RTSTRUCT (Nodos de Segmentación)
        self.rtstruct_selector = slicer.qMRMLNodeComboBox()
        self.rtstruct_selector.nodeTypes = ["vtkMRMLSegmentationNode"]  # Filtra solo RTSTRUCTs
        self.rtstruct_selector.selectNodeUponCreation = True
        self.rtstruct_selector.addEnabled = False
        self.rtstruct_selector.removeEnabled = False
        self.rtstruct_selector.noneEnabled = True
        self.rtstruct_selector.showHidden = False
        self.rtstruct_selector.showChildNodeTypes = False
        self.rtstruct_selector.setMRMLScene(slicer.mrmlScene)
        self.rtstruct_selector.setToolTip("Selecciona el conjunto de estructuras (RTSTRUCT) de la RT Nueva.")
        structuresFormLayout.addRow("RT2 Structures: ", self.rtstruct_selector)

        # --- BOTÓN PARA OCULTAR TODAS LAS ESTRUCTURAS ---
        self.hide_all_button = qt.QPushButton("Hide all Structures")
        self.hide_all_button.setStyleSheet("background-color: #34495e; color: white; padding: 5px;")
        structuresFormLayout.addRow(self.hide_all_button)

        # Conectar el botón a la función
        self.hide_all_button.connect('clicked(bool)', self.onHideAllStructures)

        # 2. Inyectar la Tabla Nativa de Segmentos de Slicer
        self.segments_table = slicer.qMRMLSegmentsTableView()
        self.segments_table.setMRMLScene(slicer.mrmlScene)
        structuresFormLayout.addRow(self.segments_table)

        # 3. Conectar el selector con la tabla
        self.rtstruct_selector.connect("currentNodeChanged(vtkMRMLNode*)", self.onRTStructSelected)

        # =========================================================================================================================================
        # PANEL 3: REIRRADIATION ANALYSIS
        # ========================================================================================================================================
        parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        parametersCollapsibleButton.text = "3. Reirradiation Calculation Settings"  # Mismo nombre que el sidebar de Streamlit
        self.layout.addWidget(parametersCollapsibleButton)
        parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

        # --- 1. Dose Volume Selectors ---
        # Selector for Dose A (RT1)
        self.dose_a_selector = slicer.qMRMLNodeComboBox()
        self.dose_a_selector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        # self.dose_a_selector.addAttribute("vtkMRMLScalarVolumeNode", "DICOM.Modality", "RTDOSE")
        self.dose_a_selector.selectNodeUponCreation = True
        self.dose_a_selector.addEnabled = False
        self.dose_a_selector.removeEnabled = False
        self.dose_a_selector.noneEnabled = False
        self.dose_a_selector.showHidden = False
        self.dose_a_selector.showChildNodeTypes = True
        self.dose_a_selector.setMRMLScene(slicer.mrmlScene)
        self.dose_a_selector.setToolTip(
            "Select the dose matrix for the Previous Radiation Course (RT1).It is recommended to use the resampled dose obtained from the rigid/deformable registration algorithms")
        parametersFormLayout.addRow("RTDOSE Previous Treatment (RT1): ", self.dose_a_selector)

        # Selector for Dose B (RT2)
        self.dose_b_selector = slicer.qMRMLNodeComboBox()
        self.dose_b_selector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        #  self.dose_b_selector.addAttribute("vtkMRMLScalarVolumeNode", "DICOM.Modality", "RTDOSE")
        self.dose_b_selector.selectNodeUponCreation = True
        self.dose_b_selector.addEnabled = False
        self.dose_b_selector.removeEnabled = False
        self.dose_b_selector.noneEnabled = False
        self.dose_b_selector.showHidden = False
        self.dose_b_selector.showChildNodeTypes = True
        self.dose_b_selector.setMRMLScene(slicer.mrmlScene)
        self.dose_b_selector.setToolTip("Select the dose matrix for the Planned Radiation Course (RT2).")
        parametersFormLayout.addRow("RTDOSE Planned Treatment (RT2): ", self.dose_b_selector)

        # --- 2. Radiobiological Parameters (Smart Defaults) ---
        # SpinBox for Alpha/Beta Ratio (ab)
        self.ab_spinbox = qt.QDoubleSpinBox()
        self.ab_spinbox.setValue(3.0)
        self.ab_spinbox.setDecimals(1)
        self.ab_spinbox.setToolTip("Alpha/Beta Ratio of the tissue under study (Gy).")
        parametersFormLayout.addRow("Alpha/Beta Ratio (Gy): ", self.ab_spinbox)

        # SpinBox for fractions_a (RT1)
        self.fractions_a_spinbox = qt.QSpinBox()
        self.fractions_a_spinbox.setValue(25)  # Valor por defecto de tu main.py
        self.fractions_a_spinbox.setMaximum(100)
        parametersFormLayout.addRow("Number of Fractions RT1: ", self.fractions_a_spinbox)

        # SpinBox for fractions_b (RT2)
        self.fractions_b_spinbox = qt.QSpinBox()
        self.fractions_b_spinbox.setValue(10)  # Valor por defecto de tu main.py para B
        self.fractions_b_spinbox.setMaximum(100)
        parametersFormLayout.addRow("Number of Fractions RT2: ", self.fractions_b_spinbox)

        # -Recovery Factor (Basado en RadReirradiation Streamlit) ---
        self.recovery_checkbox = qt.QCheckBox("Enable Partial Recovery (Time-based model)")
        self.recovery_checkbox.setChecked(False)
        self.recovery_checkbox.setToolTip(
            "The BED contribution from the previous irradiation course is reduced according its recovery assumption before being combined with the new treatment")
        parametersFormLayout.addRow(self.recovery_checkbox)

        self.months_spinbox = qt.QSpinBox()
        self.months_spinbox.setRange(0, 100)
        self.months_spinbox.setValue(12)
        self.months_spinbox.setSuffix(" months")
        self.months_spinbox.setEnabled(False)  # Inicia apagado hasta que marquen la casilla
        parametersFormLayout.addRow("Time interval (RT1 to RT2): ", self.months_spinbox)

        # Conectar la casilla para que encienda o apague el selector de meses
        self.recovery_checkbox.connect('toggled(bool)', self.months_spinbox.setEnabled)

        # Configuración volumen de Salida ---
        self.output_name_input = qt.QLineEdit()
        self.output_name_input.setPlaceholderText("Optional: Custom name for the new volume...")
        self.output_name_input.setToolTip("If you leave it blank, it will use the default name..")
        parametersFormLayout.addRow("Accumulated Dose Volume Name: ", self.output_name_input)

        # --- Apply Button ---
        self.applyButton = qt.QPushButton("Calculate Cumulative EQD2 Dose")
        self.applyButton.toolTip = "Execute the voxel-by-voxel BED/EQD2 accumulation."
        self.applyButton.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        parametersFormLayout.addRow(self.applyButton)

        # Connect button to function
        self.applyButton.connect('clicked(bool)', self.onApplyButton)

        # ==========================================================
        # PANEL 4: ANÁLISIS DOSIMÉTRICO (EQD2 METRICS)
        # ==========================================================

        metricsCollapsibleButton = ctk.ctkCollapsibleButton()
        metricsCollapsibleButton.text = "4: EQD2 Metrics and DVH"
        self.layout.addWidget(metricsCollapsibleButton)
        metricsFormLayout = qt.QFormLayout(metricsCollapsibleButton)

        # Botón para calcular
        self.calc_metrics_button = qt.QPushButton("Calculate Metrics EQD2")
        self.calc_metrics_button.setStyleSheet(
            "background-color: #9b59b6; color: white; font-weight: bold; padding: 5px;")
        metricsFormLayout.addRow(self.calc_metrics_button)

        # Tabla de resultados nativa
        self.metrics_table = qt.QTableWidget()
        self.metrics_table.setColumnCount(3)
        self.metrics_table.setHorizontalHeaderLabels(["Estructure", "Max Dose (Gy)", "Mean Dose (Gy)"])
        self.metrics_table.horizontalHeader().setSectionResizeMode(
            qt.QHeaderView.Stretch)  # Ajusta las columnas al ancho
        metricsFormLayout.addRow(self.metrics_table)

        # --- EL  BOTÓN PARA EL DVH ---
        self.plot_dvh_button = qt.QPushButton("Show DVH")
        self.plot_dvh_button.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold; padding: 5px;")
        metricsFormLayout.addRow(self.plot_dvh_button)

        # --- Botón de Exportación DICOM ---
        self.exportButton = qt.QPushButton("Export EQD2 to DICOM ")
        self.exportButton.toolTip = "Exports the calculated EQD2 dose with the original patient's DICOM tags."
        self.exportButton.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 5px;")
        self.exportButton.enabled = False  # Nace apagado hasta que se calcule la dosis

        # Asumiendo que parametersFormLayout es el layout donde tienes tus botones principales
        # Ajusta el nombre del layout si lo llamaste diferente en esta sección
        metricsFormLayout.addRow(self.exportButton)

        # Conectar el botón a la función
        self.calc_metrics_button.connect('clicked(bool)', self.onCalculateMetrics)
        self.plot_dvh_button.connect('clicked(bool)', self.onGenerateDVH)
        self.exportButton.connect('clicked(bool)', self.onExportDICOMClicked)

        # Empuja todo hacia arriba para que quede ordenado
        self.layout.addStretch(1)

    # ====================================================================================================================
    # FUNCIONES CONECTADAS
    # ==================================================================================================================

    def onCenterButtonClicked(self):
        fixed_ct = self.fixed_ct_selector.currentNode()
        moving_ct = self.moving_ct_selector.currentNode()

        # 1. Validación de seguridad básica
        if not fixed_ct or not moving_ct:
            slicer.util.warningDisplay("Please select the Fixed CT and Moving CT first.")
            return

        # 2. Validación: Evitar la ilusión óptica de Slicer
        if fixed_ct == moving_ct:
            slicer.util.warningDisplay("Fixed CT and Moving CT cannot be the exact same volume.")
            return

        import numpy as np
        import vtk

        try:
            # ==========================================================
            # NUEVO: VALIDACIÓN ANTI "CLOSE SCENE" (Exorcismo de Fantasmas)
            # ==========================================================
            if self.manual_transform_node:
                try:
                    # Intentamos buscar el nodo en la escena actual
                    if not slicer.mrmlScene.GetNodeByID(self.manual_transform_node.GetID()):
                        self.manual_transform_node = None  # Estaba borrado, reseteamos la variable
                except:
                    # Si el C++ fue destruido, pedir el GetID falla. Lo atrapamos aquí.
                    self.manual_transform_node = None

            # Si la variable está vacía (o la acabamos de vaciar), creamos un volante nuevo y real
            if not self.manual_transform_node:
                self.manual_transform_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode",
                                                                                "Manual_PreAlign")
            # ==========================================================

            moving_ct.SetAndObserveTransformNodeID(None)
            slicer.app.processEvents()

            # Cálculo de centros
            def get_true_center(volume_node):
                matrix = vtk.vtkMatrix4x4()
                volume_node.GetIJKToRASMatrix(matrix)
                image_data = volume_node.GetImageData()
                if image_data:
                    dims = image_data.GetDimensions()
                    center_ijk = [dims[0] / 2.0, dims[1] / 2.0, dims[2] / 2.0, 1.0]
                    center_ras = matrix.MultiplyPoint(center_ijk)
                    return np.array(center_ras[0:3])
                else:
                    bounds = np.zeros(6)
                    volume_node.GetBounds(bounds)
                    return np.array(
                        [(bounds[0] + bounds[1]) / 2.0, (bounds[2] + bounds[3]) / 2.0, (bounds[4] + bounds[5]) / 2.0])

            cf = get_true_center(fixed_ct)
            cm = get_true_center(moving_ct)

            self.base_translation = cf - cm

            # Resetear barras visualmente (sin disparar el evento)
            self.sliderX.blockSignals(True);
            self.sliderY.blockSignals(True);
            self.sliderZ.blockSignals(True)
            self.sliderX.value = 0;
            self.sliderY.value = 0;
            self.sliderZ.value = 0;
            self.sliderX.blockSignals(False);
            self.sliderY.blockSignals(False);
            self.sliderZ.blockSignals(False)

            self.updateManualTransform(0, 0, 0)
            moving_ct.SetAndObserveTransformNodeID(self.manual_transform_node.GetID())

            slicer.util.setSliceViewerLayers(background=fixed_ct, foreground=moving_ct, foregroundOpacity=0.5)
            slicer.modules.markups.logic().JumpSlicesToLocation(cf[0], cf[1], cf[2], True)

            # Despertar las barras
            self.sliderX.enabled = True
            self.sliderY.enabled = True
            self.sliderZ.enabled = True

        except Exception as e:
            slicer.util.errorDisplay(f"Error during Auto-Center: {str(e)}\nPlease check if the CT is fully loaded.")

    def onSliderValueChanged(self, value):
        # Bloque de seguridad para cuando mueves las barras
        if self.manual_transform_node:
            try:
                # Comprobar que el volante existe en la escena antes de inyectarle movimiento
                if slicer.mrmlScene.GetNodeByID(self.manual_transform_node.GetID()):
                    self.updateManualTransform(self.sliderX.value, self.sliderY.value, self.sliderZ.value)
            except:
                pass  # Ignorar silenciosamente si el nodo es un fantasma

    def updateManualTransform(self, dx, dy, dz):
        import vtk
        transform = vtk.vtkTransform()
        # Sumamos el teletransporte inicial + lo que muevas en las barras
        transform.Translate(self.base_translation[0] + dx,
                            self.base_translation[1] + dy,
                            self.base_translation[2] + dz)
        self.manual_transform_node.SetMatrixTransformToParent(transform.GetMatrix())

    def onApplyButton(self):
        # 1. Recolectar los datos que el usuario puso en la interfaz
        # 1. Recolectar los datos que el usuario puso en la interfaz
        dose_a_node = self.dose_a_selector.currentNode()
        dose_b_node = self.dose_b_selector.currentNode()
        ab = self.ab_spinbox.value
        fx_a = self.fractions_a_spinbox.value
        fx_b = self.fractions_b_spinbox.value

        # Nuevos valores de tiempo
        use_recovery = self.recovery_checkbox.isChecked()
        months = self.months_spinbox.value

        # Leemos el nombre personalizado
        custom_name = self.output_name_input.text.strip()

        # 2. Enviar los datos a la Lógica (el cerebro) envueltos en un bloque de seguridad
        try:
            # Mostramos un mensaje temporal en la barra de estado de Slicer
            slicer.util.showStatusMessage("Calculating BED/EQD2 voxel by voxel...")

            # ¡Llamamos a la magia!
            resultado = self.logic.procesarDosis(dose_a_node, dose_b_node, ab, fx_a, fx_b, use_recovery, months,
                                                 custom_name)

            # 1. Guardar el resultado en la memoria del Widget (para el botón de exportar)
            self.eqd2_node = resultado  # (Asegúrate de usar el mismo nombre de la variable de arriba)
            # Encendemos el botón verde de exportar
            self.exportButton.enabled = True

            slicer.util.showStatusMessage("¡Calculation completed!")
            slicer.util.infoDisplay("¡Cálculation of accumulated EQD2 completed con successfully!",
                                    windowTitle="RadReirradiation")
        except Exception as e:
            # Si algo falla (ej. tamaños distintos), Slicer no se cierra, solo muestra un aviso
            slicer.util.errorDisplay(f"Calculation Error:\n{str(e)}", windowTitle="RadReirradiation Error")

    def onRegisterButton(self):
        fixed_ct = self.fixed_ct_selector.currentNode()
        moving_ct = self.moving_ct_selector.currentNode()
        moving_dose = self.moving_dose_selector.currentNode()
        fixed_dose = self.fixed_dose_selector.currentNode()

        # Leemos si el usuario quiere deformable o affine
        use_deformable = self.deformable_checkbox.isChecked()
        use_affine = self.affine_checkbox.isChecked()  # <

        if not fixed_ct or not moving_ct or not moving_dose:
            slicer.util.errorDisplay("Please select the two CTs and the Dose you wish to align.",
                                     windowTitle="Data is missing")
            return

        try:
            if use_deformable:
                slicer.util.showStatusMessage(
                    "Running Deformable Registration (May take minutes) (BRAINSFit) Please wait...")
            else:
                slicer.util.showStatusMessage("Running Rigid Registration (BRAINSFit) Please wait...")

            # Llamamos a la lógica
            # self.logic.runFastRegistration(fixed_ct, moving_ct, moving_dose, fixed_dose, use_deformable)
            # 1. CAPTURAMOS el resultado del registro
            aligned_dose_node = self.logic.runFastRegistration(fixed_ct, moving_ct, moving_dose, fixed_dose,
                                                               use_deformable, use_affine, self.manual_transform_node)

            # 2. MAGIA UX: Auto-asignamos los volúmenes a los selectores del PASO 2
            self.dose_a_selector.setCurrentNode(aligned_dose_node)
            self.dose_b_selector.setCurrentNode(fixed_dose)

            slicer.util.showStatusMessage("registration and Dose resampling completed!")
            slicer.util.infoDisplay(
                "Successful alignment.\n\nLook for the new Dose volume with the suffix '_Registered' in your Base Dose (RT1) list to perform the calculation.",
                windowTitle="RadReirradiation FastReg")
        except Exception as e:
            slicer.util.errorDisplay(f"Error during image registration:\n{str(e)}",
                                     windowTitle="RadReirradiation Error")

    def onRTStructSelected(self, node):
        """Conecta las estructuras a la tabla usando la visualización nativa de SlicerRT"""
        if node:
            # 1. Conectamos el nodo directamente a la tabla
            self.segments_table.setSegmentationNode(node)

            # 2. Aseguramos el interruptor maestro y ajustamos la estética clínica
            display_node = node.GetDisplayNode()
            if display_node:
                display_node.SetVisibility(True)
                display_node.SetVisibility2D(True)

                # Ajustamos la opacidad para que no tape el mapa de calor de tu dosis
                display_node.SetOpacity2DFill(0.3)
                display_node.SetOpacity2DOutline(1.0)

            slicer.util.showStatusMessage("Structures successfully linked to the table!")

        else:
            # Si se selecciona "None", vaciamos la tabla
            self.segments_table.setSegmentationNode(None)

    def onHideAllStructures(self):
        slicer.util.showStatusMessage("Toggling individual structures...")
        slicer.app.processEvents()

        segmentation_nodes = slicer.util.getNodesByClass("vtkMRMLSegmentationNode")
        for node in segmentation_nodes:
            display_node = node.GetDisplayNode()
            if display_node:
                # 1. OBLIGATORIO: Mantener el contenedor padre encendido para que la tabla funcione
                display_node.SetVisibility(True)

                # 2. Determinar si hay al menos un "ojito" encendido internamente
                any_visible = False
                segmentation = node.GetSegmentation()
                for i in range(segmentation.GetNumberOfSegments()):
                    segment_id = segmentation.GetNthSegmentID(i)
                    if display_node.GetSegmentVisibility(segment_id):
                        any_visible = True
                        break

                # 3. Sincronizar la interfaz: Apagar o encender TODOS los ojitos individuales
                if any_visible:
                    display_node.SetAllSegmentsVisibility(False)
                else:
                    display_node.SetAllSegmentsVisibility(True)

        slicer.util.showStatusMessage("")

    def onCalculateMetrics(self):
        """Calcula métricas forzando la actualización de los datos de dosis visibles"""
        import numpy as np

        # Identificar el volumen activo en el visor rojo
        layoutManager = slicer.app.layoutManager()
        sliceWidget = layoutManager.sliceWidget('Red')
        compositeNode = sliceWidget.sliceLogic().GetSliceCompositeNode()

        # IMPORTANTE: Tomamos el volumen del Foreground (lo que estás viendo)
        foreground_id = compositeNode.GetForegroundVolumeID()
        if not foreground_id:
            slicer.util.warningDisplay(
                "There is no active volume in the foreground layer. Make sure you have the dose map selected.")
            return

        eqd2_dose_node = slicer.mrmlScene.GetNodeByID(foreground_id)

        slicer.util.showStatusMessage(f"Calculating about: {eqd2_dose_node.GetName()}...")
        slicer.app.processEvents()

        segmentation_node = self.rtstruct_selector.currentNode()
        if not segmentation_node:
            slicer.util.warningDisplay("Select a valid RTSTRUCT in Panel 3.")
            return

        segmentation = segmentation_node.GetSegmentation()
        display_node = segmentation_node.GetDisplayNode()

        self.metrics_table.setRowCount(0)
        row = 0

        # EXTRAER LA MATRIZ DE DOSIS ACTUALIZADA
        dose_array = slicer.util.arrayFromVolume(eqd2_dose_node)

        for i in range(segmentation.GetNumberOfSegments()):
            segment_id = segmentation.GetNthSegmentID(i)
            if display_node and not display_node.GetSegmentVisibility(segment_id):
                continue

            segment_name = segmentation.GetSegment(segment_id).GetName()

            # Resamplear el segmento a la resolución del NUEVO volumen de dosis
            segment_array = slicer.util.arrayFromSegmentBinaryLabelmap(segmentation_node, segment_id, eqd2_dose_node)

            if segment_array is not None:
                organ_dose_values = dose_array[segment_array > 0]
                if len(organ_dose_values) > 0:
                    max_dose = np.max(organ_dose_values)
                    mean_dose = np.mean(organ_dose_values)

                    self.metrics_table.insertRow(row)
                    self.metrics_table.setItem(row, 0, qt.QTableWidgetItem(segment_name))

                    item_max = qt.QTableWidgetItem(f"{max_dose:.2f}")
                    item_max.setTextAlignment(qt.Qt.AlignCenter)
                    self.metrics_table.setItem(row, 1, item_max)

                    item_mean = qt.QTableWidgetItem(f"{mean_dose:.2f}")
                    item_mean.setTextAlignment(qt.Qt.AlignCenter)
                    self.metrics_table.setItem(row, 2, item_mean)

                    row += 1

        slicer.util.showStatusMessage("Metrics updated correctly.")

    def onGenerateDVH(self):
        """Genera el DVH eliminando datos previos de la escena"""
        import numpy as np
        import vtk

        layoutManager = slicer.app.layoutManager()
        sliceWidget = layoutManager.sliceWidget('Red')
        compositeNode = sliceWidget.sliceLogic().GetSliceCompositeNode()

        foreground_id = compositeNode.GetForegroundVolumeID()
        if not foreground_id:
            slicer.util.warningDisplay("There is no active volume in the foreground layer.")
            return

        eqd2_dose_node = slicer.mrmlScene.GetNodeByID(foreground_id)

        # ==========================================================
        # LIMPIEZA PROFUNDA (GARBAGE COLLECTOR)
        # ==========================================================
        # Borramos Chart, Tablas y Series previas para no saturar la RAM ni el panel de datos
        nodes_to_delete = slicer.util.getNodesByClass("vtkMRMLPlotChartNode") + \
                          slicer.util.getNodesByClass("vtkMRMLTableNode") + \
                          slicer.util.getNodesByClass("vtkMRMLPlotSeriesNode")

        for node in nodes_to_delete:
            if "DVH" in node.GetName():
                slicer.mrmlScene.RemoveNode(node)
        # ==========================================================

        plotChartNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotChartNode", "DVH_EQD2_Chart")
        # Le ponemos el nombre del volumen actual al título del gráfico para que sepas qué estás viendo
        plotChartNode.SetTitle(f"Dose Volume Histogram ({eqd2_dose_node.GetName()})")
        plotChartNode.SetXAxisTitle("Dose EQD2 (Gy)")
        plotChartNode.SetYAxisTitle("Relative Volume (%)")

        segmentation_node = self.rtstruct_selector.currentNode()
        if not segmentation_node: return

        segmentation = segmentation_node.GetSegmentation()
        display_node = segmentation_node.GetDisplayNode()

        dose_array = slicer.util.arrayFromVolume(eqd2_dose_node)

        for i in range(segmentation.GetNumberOfSegments()):
            segment_id = segmentation.GetNthSegmentID(i)
            if display_node and not display_node.GetSegmentVisibility(segment_id):
                continue

            segment_array = slicer.util.arrayFromSegmentBinaryLabelmap(segmentation_node, segment_id, eqd2_dose_node)
            if segment_array is None: continue

            organ_dose_values = dose_array[segment_array > 0]
            if len(organ_dose_values) == 0: continue

            # Cálculo de DVH
            max_dose = np.max(organ_dose_values)
            bins = np.arange(0, max_dose + 0.2, 0.1)
            hist, _ = np.histogram(organ_dose_values, bins=bins)
            cum_vol_percent = (np.cumsum(hist[::-1])[::-1] / len(organ_dose_values)) * 100.0

            # Crear Tabla Única
            segment_name = segmentation.GetSegment(segment_id).GetName()
            color = segmentation.GetSegment(segment_id).GetColor()

            tableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", f"DVH_Data_{segment_name}")
            dose_col = vtk.vtkDoubleArray();
            dose_col.SetName("Dose")
            vol_col = vtk.vtkDoubleArray();
            vol_col.SetName("Volume")

            for d, v in zip(bins[:-1], cum_vol_percent):
                dose_col.InsertNextValue(d)
                vol_col.InsertNextValue(v)

            tableNode.AddColumn(dose_col)
            tableNode.AddColumn(vol_col)

            seriesNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotSeriesNode", segment_name)
            seriesNode.SetAndObserveTableNodeID(tableNode.GetID())
            seriesNode.SetXColumnName("Dose")
            seriesNode.SetYColumnName("Volume")
            seriesNode.SetPlotType(slicer.vtkMRMLPlotSeriesNode.PlotTypeScatter)
            seriesNode.SetMarkerStyle(slicer.vtkMRMLPlotSeriesNode.MarkerStyleNone)
            seriesNode.SetColor(color[0], color[1], color[2])

            plotChartNode.AddAndObservePlotSeriesNodeID(seriesNode.GetID())

        # Configurar Layout y mostrar
        layoutManager.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpPlotView)
        plotWidget = layoutManager.plotWidget(0)
        plotViewNode = plotWidget.mrmlPlotViewNode()
        plotViewNode.SetPlotChartNodeID(plotChartNode.GetID())

        slicer.util.showStatusMessage("¡DVH Successfully generated!")

    def onExportDICOMClicked(self):
        fixed_ct = self.fixed_ct_selector.currentNode()
        fixed_dose = self.fixed_dose_selector.currentNode()

        if not hasattr(self, 'eqd2_node') or not self.eqd2_node:
            slicer.util.warningDisplay("Please calculate the EQD2 dose first.")
            return

        try:
            shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
            eqd2_item_id = shNode.GetItemByDataNode(self.eqd2_node)
            fixed_ct_item_id = shNode.GetItemByDataNode(fixed_ct)

            # 1. Copiar el "ADN" de la dosis original
            attrNames = fixed_dose.GetAttributeNames()
            if attrNames:
                for attrName in attrNames:
                    if attrName.startswith("DICOM."):
                        self.eqd2_node.SetAttribute(attrName, fixed_dose.GetAttribute(attrName))

            self.eqd2_node.SetAttribute("DICOM.Modality", "RTDOSE")
            self.eqd2_node.SetAttribute("DICOM.SeriesDescription", "RadReirradiation_EQD2_Sum")
            self.eqd2_node.RemoveAttribute("DICOM.instanceUIDs")

            # 2. Mover la Dosis para que sea "hermana" exacta del CT en la carpeta del paciente
            parent_item_id = shNode.GetItemParent(fixed_ct_item_id)
            shNode.SetItemParent(eqd2_item_id, parent_item_id)
            shNode.SetItemAttribute(eqd2_item_id, "DICOM.Modality", "RTDOSE")

            # 3. Abrir ventana de exportación
            slicer.modules.dicom.widgetRepresentation()
            exportDialog = slicer.qSlicerDICOMExportDialog(None)
            exportDialog.setMRMLScene(slicer.mrmlScene)
            exportDialog.execDialog()

        except Exception as e:
            slicer.util.errorDisplay(f"Export Error: {str(e)}")


# ==========================================================
# 3. LÓGICA MATEMÁTICA (CEREBRO)
# ==========================================================

class RadReirradiationLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        ScriptedLoadableModuleLogic.__init__(self)

    def runFastRegistration(self, fixed_ct, moving_ct, moving_dose, fixed_dose, use_deformable=False, use_affine=False,
                            manual_transform=None):
        # ==========================================================
        # UX: INICIAR VENTANA DE CARGA Y CURSOR DE ESPERA
        # ==========================================================
        slicer.app.setOverrideCursor(qt.Qt.WaitCursor)  # Cambia el ratón a reloj de arena

        # Creamos una barra de progreso "infinita" (maximum=0)
        progress = slicer.util.createProgressDialog(
            parent=slicer.util.mainWindow(),
            labelText="Calculating Image Registration......\nPlease wait, Slicer will appear frozen for a couple of minutes.",
            windowTitle="RadReirradiation Processing",
            value=0, maximum=0
        )
        progress.show()
        slicer.app.processEvents()  # Vital: Fuerza a Slicer a dibujar la ventana antes de congelarse
        try:
            # 1. Crear el "recipiente" donde se guardará el resultado matemático de la fusión
            transform_name = f"Transform_{moving_ct.GetName()}_to_{fixed_ct.GetName()}"
            final_transform = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", transform_name)

            # 2. Configurar el tipo de transformación dinámicamente según la interfaz
            fases_registro = ["Rigid"]  # Rígido siempre es obligatorio como base

            if use_affine:
                fases_registro.append("Affine")

            if use_deformable:
                fases_registro.append("BSpline")

            # Unir las palabras con comas (Ej: "Rigid,BSpline" si Affine está apagado)
            t_types = ",".join(fases_registro)

            tasa_muestreo = 0.01 if use_deformable else 0.02

            # 3. Diccionario de Parámetros de BRAINSFit con "Balance Clínico"
            parameters = {
                "fixedVolume": fixed_ct.GetID(),
                "movingVolume": moving_ct.GetID(),
                "transformType": t_types,
                "maskProcessingMode": "NOMASK",
                "samplingPercentage": tasa_muestreo,  # 2% de los píxeles (Estándar comercial para velocidad/precisión)
                "numberOfIterations": 500,  # Límite de intentos para evitar ciclos infinitos
                "minimumStepLength": 0.005,  # Detenerse temprano si el "match" óseo ya es perfecto
            }

            # 4. El Puente: ¿El usuario ajustó las barras manuales?
            if manual_transform:
                parameters["initialTransform"] = manual_transform.GetID()
                parameters["initializeTransformMode"] = "Off"  # Respetar el ajuste manual del usuario
            else:
                parameters[
                    "initializeTransformMode"] = "useGeometryAlign"  # Si no usó las barras, intentar centrar automático

            # 5. Decirle al motor de registro DÓNDE GUARDAR el resultado
            if use_deformable:
                parameters["bsplineTransform"] = final_transform.GetID()
                parameters["splineGridSize"] = [5, 5, 5]
            else:
                parameters["linearTransform"] = final_transform.GetID()

            # ==========================================================
            # 6. EJECUTAR EL MOTOR DE REGISTRO DE IMÁGENES (BRAINSFit)
            # ==========================================================
            brainsFit = slicer.modules.brainsfit
            cliNode = slicer.cli.runSync(brainsFit, None, parameters)

            if cliNode.GetStatus() & cliNode.ErrorsMask:
                raise ValueError("The image registration engine (BRAINSFit) failed.")

            # ==========================================================
            # 7. MOVER LA DOSIS ANTIGUA (BRAINSResample)
            # ==========================================================
            # Preparar un volumen clonado vacío para recibir la nueva dosis deformada
            output_dose_name = f"{moving_dose.GetName()}_Registered"
            volumesLogic = slicer.modules.volumes.logic()
            outputDose = volumesLogic.CloneVolume(slicer.mrmlScene, fixed_dose, output_dose_name)
            outputDose.SetAttribute("DICOM.Modality", "RTDOSE")

            # Configurar el motor de re-muestreo pasándole el final_transform obtenido arriba
            resample_params = {
                "inputVolume": moving_dose.GetID(),
                "referenceVolume": fixed_dose.GetID(),
                "outputVolume": outputDose.GetID(),
                "warpTransform": final_transform.GetID(),  # Aplicar el mismo movimiento de los huesos a la dosis
                "interpolationMode": "Linear",
                "pixelType": "float"
            }

            cliNodeResample = slicer.cli.runSync(slicer.modules.brainsresample, None, resample_params)

            if cliNodeResample.GetStatus() & cliNodeResample.ErrorsMask:
                raise ValueError("The Dose resample (BRAINSResample) failed.")

            # ==========================================================
            # 8. ACTUALIZAR LA PANTALLA
            # ==========================================================
            # Enganchar el TAC Antiguo a la transformación final para que el usuario vea el resultado
            moving_ct.SetAndObserveTransformNodeID(final_transform.GetID())
            slicer.util.setSliceViewerLayers(background=fixed_ct, foreground=moving_ct, foregroundOpacity=0.5)

            return outputDose

        finally:
            # ==========================================================
            # UX: RESTAURAR INTERFAZ (Incluso si hay un error)
            # ==========================================================
            progress.close()
            slicer.app.restoreOverrideCursor()  # Regresa el cursor a la normalidad

    def procesarDosis(self, dose_a_node, dose_b_node, ab, fx_a, fx_b, use_recovery, months, custom_name=""):
        import numpy as np

        # --- PASO A: Validaciones Clínicas ---
        if not dose_a_node or not dose_b_node:
            raise ValueError("Please select both dose matrices (RT1 y RT2).")
        if fx_a <= 0 or fx_b <= 0:
            raise ValueError("The number of fractions must be greater than zero.")
        if ab <= 0:
            raise ValueError("The Alpha/Beta value must be greater than zero.")

        # --- PASO B: Extracción de Vóxeles ---
        array_a = slicer.util.arrayFromVolume(dose_a_node)
        array_b = slicer.util.arrayFromVolume(dose_b_node)

        if array_a.shape != array_b.shape:
            raise ValueError(
                f"The Matrix dimensions do not match..\nDose RT1: {array_a.shape}\nDose RT2: {array_b.shape}\nYou must register and resample the images beforehand.")

        # --- PASO C: Matemática Radiobiológica ---
        d_a = array_a / fx_a
        d_b = array_b / fx_b
        bed_a = array_a * (1.0 + (d_a / ab))
        bed_b = array_b * (1.0 + (d_b / ab))
        # bed_total = bed_a + bed_b
        #  eqd2_total = bed_total * (ab / (2.0 + ab))
        # --- Lógica de Recuperación (Misma de tu Streamlit) ---
        recovery = 0.0
        if use_recovery:
            if months < 6:
                recovery = 0.0
            elif months < 12:
                recovery = 0.25
            elif months < 24:
                recovery = 0.50
            else:
                recovery = 0.65

        # Calculamos el BED efectivo restando la recuperación
        effective_bed_a = bed_a * (1.0 - recovery)

        # Sumamos el BED viejo con descuento + el BED nuevo
        bed_total = effective_bed_a + bed_b
        eqd2_total = bed_total * (ab / (2.0 + ab))

        # --- PASO D: Retorno a Slicer ---
        volumesLogic = slicer.modules.volumes.logic()
        # nuevo_nombre = f"RadReirradiation_EQD2_Acumulado_ab{int(ab)}"

        # Aquí aplicamos la lógica del nombre
        if custom_name:
            nuevo_nombre = custom_name
        else:
            nuevo_nombre = f"RadReirradiation_EQD2_Accumulated_ab{int(ab)}"

        eqd2_node = volumesLogic.CloneVolume(slicer.mrmlScene, dose_a_node, nuevo_nombre)
        eqd2_node.SetAttribute("DICOM.Modality", "RTDOSE")
        slicer.util.updateVolumeFromArray(eqd2_node, eqd2_total)

        # --- PASO E: AUTOMATIZACIÓN VISUAL ---
        # 1. Encontrar la dosis máxima para escalar los colores automáticamente
        dosis_maxima = np.max(eqd2_total)

        # 2. Configurar el "Display Node" (el pintor de Slicer)
        display_node = eqd2_node.GetDisplayNode()
        if display_node is None:
            eqd2_node.CreateDefaultDisplayNodes()
            display_node = eqd2_node.GetDisplayNode()

        # 3. Aplicar paleta de colores de dosis (Arcoíris)
        # display_node.SetAndObserveColorNodeID('vtkMRMLColorTableNodeRainbow')
        # ==========================================================
        # 3. CREAR Y ASIGNAR MAPA DE COLORES ESTILO "ECLIPSE TPS"
        # ==========================================================
        color_name = "Eclipse_Dose_Wash"
        color_node = slicer.mrmlScene.GetFirstNodeByName(color_name)

        # Si el mapa no existe en la escena, lo creamos desde cero
        if not color_node:
            color_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLColorTableNode", color_name)
            color_node.SetTypeToUser()
            color_node.SetNumberOfColors(256)

            # Usamos una función de transferencia para crear el degradado suave
            ctf = vtk.vtkColorTransferFunction()
            ctf.AddRGBPoint(0.00, 0.0, 0.0, 0.6)  # 0%   - Azul Oscuro (Bajas dosis)
            ctf.AddRGBPoint(0.25, 0.0, 0.8, 1.0)  # 25%  - Cyan
            ctf.AddRGBPoint(0.50, 0.0, 1.0, 0.0)  # 50%  - Verde
            ctf.AddRGBPoint(0.75, 1.0, 1.0, 0.0)  # 75%  - Amarillo
            ctf.AddRGBPoint(0.90, 1.0, 0.5, 0.0)  # 90%  - Naranja
            ctf.AddRGBPoint(1.00, 1.0, 0.0, 0.0)  # 100% - Rojo (Altas dosis)

            # Llenamos la paleta de Slicer con los 256 colores interpolados
            for i in range(256):
                r, g, b = ctf.GetColor(i / 255.0)
                color_node.SetColor(i, str(i), r, g, b, 1.0)  # El 1.0 es la opacidad base

        # Le aplicamos nuestro nuevo mapa de colores al volumen de dosis
        display_node.SetAndObserveColorNodeID(color_node.GetID())
        # ==========================================================

        # 4. Ajustar umbral: Hacer transparente todo lo que esté por debajo de 2 Gy
        umbral_minimo = 2.0
        display_node.SetAutoWindowLevel(False)
        display_node.SetWindowLevelMinMax(umbral_minimo, dosis_maxima)
        display_node.SetApplyThreshold(1)
        display_node.SetLowerThreshold(umbral_minimo)
        display_node.SetUpperThreshold(dosis_maxima)

        # 5. Inyectar automáticamente el mapa de calor sobre las vistas 2D
        slicer.util.setSliceViewerLayers(foreground=eqd2_node, foregroundOpacity=0.4)

        # 6. CREAR Y MOSTRAR LA LEYENDA (SCALAR BAR)
        try:
            # Invoca el motor de leyendas de Slicer y lo ancla a nuestro volumen
            color_legend = slicer.modules.colors.logic().AddDefaultColorLegendDisplayNode(eqd2_node)
            color_legend.SetTitleText("Dose EQD2 (Gy)")
        except Exception as e:
            # En caso de que se use una versión antigua de Slicer que no soporte este método
            print(f"Notice: The legend could not be generated automatically. {e}")

        return eqd2_node


# ==========================================================
# 4. PRUEBAS AUTOMATIZADAS
# ==========================================================
class RadReirradiationTest(ScriptedLoadableModuleTest):
    def setUp(self):
        slicer.mrmlScene.Clear()

    def runTest(self):
        pass
