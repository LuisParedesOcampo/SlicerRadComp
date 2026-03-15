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
class SlicerRadComp(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "RadComp Reirradiation analysis"  # Nombre que verás en Slicer
        self.parent.categories = ["Radiotherapy"]  # Se creará esta categoría en el menú
        self.parent.dependencies = []
        self.parent.contributors = ["Luis Paredes, Clinical Medical Physicist "]
        self.parent.helpText = "A clinical tool for Reirradiation calculations, visit the online version https://radcomp.streamlit.app ."
        self.parent.acknowledgementText = "Basado en la librería radcomp."


# ==========================================================
# 2. INTERFAZ GRÁFICA (WIDGET / GUI)
# ==========================================================
class SlicerRadCompWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)
        self.logic = None

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        self.logic = SlicerRadCompLogic()

        # ==========================================
        # PANEL 1: FAST IMAGE REGISTRATION
        # ==========================================
        registrationCollapsibleButton = ctk.ctkCollapsibleButton()
        registrationCollapsibleButton.text = "1. Fast Registration & Resample (Optional)"
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
        self.fixed_dose_selector.setToolTip("The Dosage of the NEW plan. Its geometric matrix will be used as a template.")
        registrationFormLayout.addRow("RTDOSE planned treatment RT2 (Fixed): ", self.fixed_dose_selector)

        # Casilla para Registro Deformable
        self.deformable_checkbox = qt.QCheckBox("Enable Deformable (B-Spline) Registration, It will take several minutes..")
        self.deformable_checkbox.setChecked(False)
        self.deformable_checkbox.setToolTip(
            "First calculate Rigid, then apply Deformable. This may take several minutes.")
        registrationFormLayout.addRow(self.deformable_checkbox)

        # Botón Azul de Registro
        self.registerButton = qt.QPushButton("Auto-Registration and Resample Dose")
        self.registerButton.toolTip = "It performs an automatic hard registration and adjusts the dose grid.."
        self.registerButton.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        registrationFormLayout.addRow(self.registerButton)

        # Connect Register button to function
        self.registerButton.connect('clicked(bool)', self.onRegisterButton)

        # Le cambiamos el texto al panel de abajo para  el "Paso 2"
        # parametersCollapsibleButton.text = "2. Biological Calculation Settings"
        # --- Collapsible Panel ---
        parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        parametersCollapsibleButton.text = "2. Reirradiation Calculation Settings"  # Mismo nombre que el sidebar de Streamlit
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
        self.dose_a_selector.setToolTip("Select the dose matrix for the Previous Radiation Course (RT1).It is recommended to use the resampled dose obtained from the rigid/deformable registration algorithms")
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

        # --- 3. Time / Recovery Factor (Basado en RadComp Streamlit) ---
        self.recovery_checkbox = qt.QCheckBox("Enable Partial Recovery (Time-based model)")
        self.recovery_checkbox.setChecked(False)
        self.recovery_checkbox.setToolTip("The BED contribution from the previous irradiation course is reduced according its recovery assumption before being combined with the new treatment")
        parametersFormLayout.addRow(self.recovery_checkbox)

        self.months_spinbox = qt.QSpinBox()
        self.months_spinbox.setRange(0, 100)
        self.months_spinbox.setValue(12)
        self.months_spinbox.setSuffix(" months")
        self.months_spinbox.setEnabled(False)  # Inicia apagado hasta que marquen la casilla
        parametersFormLayout.addRow("Time interval (RT1 to RT2): ", self.months_spinbox)

        # Conectar la casilla para que encienda o apague el selector de meses
        self.recovery_checkbox.connect('toggled(bool)', self.months_spinbox.setEnabled)

        # --- 4. Configuración de Salida ---
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

        # Empuja todo hacia arriba para que quede ordenado
        self.layout.addStretch(1)

    def onApplyButton(self):
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
            self.logic.procesarDosis(dose_a_node, dose_b_node, ab, fx_a, fx_b, use_recovery, months,custom_name)

            slicer.util.showStatusMessage("¡Calculation completed!")
            slicer.util.infoDisplay("¡Cálculation of accumulated EQD2 completed con successfully!", windowTitle="RadComp")
        except Exception as e:
            # Si algo falla (ej. tamaños distintos), Slicer no se cierra, solo muestra un aviso
            slicer.util.errorDisplay(f"Calculation Error:\n{str(e)}", windowTitle="RadComp Error")

    def onRegisterButton(self):
        fixed_ct = self.fixed_ct_selector.currentNode()
        moving_ct = self.moving_ct_selector.currentNode()
        moving_dose = self.moving_dose_selector.currentNode()
        fixed_dose = self.fixed_dose_selector.currentNode()

        # Leemos si el usuario quiere deformable
        use_deformable = self.deformable_checkbox.isChecked()

        if not fixed_ct or not moving_ct or not moving_dose:
            slicer.util.errorDisplay("Please select the two CTs and the Dose you wish to align.",
                                     windowTitle="Data is missing")
            return

        try:
            if use_deformable:
                slicer.util.showStatusMessage("Running Deformable Registration (May take minutes) (BRAINSFit) Please wait...")
            else:
                slicer.util.showStatusMessage("Running Rigid Registration (BRAINSFit) Please wait...")



            # Llamamos a la lógica
            #self.logic.runFastRegistration(fixed_ct, moving_ct, moving_dose, fixed_dose, use_deformable)
            # 1. CAPTURAMOS el resultado del registro
            aligned_dose_node = self.logic.runFastRegistration(fixed_ct, moving_ct, moving_dose, fixed_dose,use_deformable)

            # 2. MAGIA UX: Auto-asignamos los volúmenes a los selectores del PASO 2
            self.dose_a_selector.setCurrentNode(aligned_dose_node)
            self.dose_b_selector.setCurrentNode(fixed_dose)

            slicer.util.showStatusMessage("registration and Dose resampling completed!")
            slicer.util.infoDisplay(
                "Successful alignment.\n\nLook for the new Dose volume with the suffix '_Aligned' in your Base Dose (RT1) list to perform the calculation.",
                windowTitle="RadComp FastReg")
        except Exception as e:
            slicer.util.errorDisplay(f"Error during image registration:\n{str(e)}", windowTitle="RadComp Error")


# ==========================================================
# 3. LÓGICA MATEMÁTICA (CEREBRO)
# ==========================================================

class SlicerRadCompLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        ScriptedLoadableModuleLogic.__init__(self)

    def runFastRegistration(self, fixed_ct, moving_ct, moving_dose, fixed_dose,use_deformable=False):
        # 1. Crear un nodo contenedor para la matriz de transformación
        transform_name = f"Transform_{moving_ct.GetName()}_to_{fixed_ct.GetName()}"
       # transformNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLinearTransformNode", transform_name) #funciona para regisro rigido lienal
        transformNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", transform_name)

        # 2. Configurar el motor BRAINSFit (Registro Rígido)
        parameters = {
            "fixedVolume": fixed_ct.GetID(),
            "movingVolume": moving_ct.GetID(),
           # "linearTransform": transformNode.GetID(),
            "useRigid": True,  # Siempre hace un pre-alineamiento rígido
            "initializeTransformMode": "useGeometryAlign",  # Alinea usando el centro geométrico inicial
            "maskProcessingMode": "NOMASK"
        }

        if use_deformable:
            parameters["bsplineTransform"] = transformNode.GetID()  # Canal elástico
            parameters["useBSpline"] = True
            parameters["splineGridSize"] = [3, 3, 3]  # Lista nativa de Python
        else:
            parameters["linearTransform"] = transformNode.GetID()  # Canal rígido


        # Ejecutar en modo síncrono (congela la pantalla unos segundos hasta que termina)
        brainsFit = slicer.modules.brainsfit
        cliNode = slicer.cli.runSync(brainsFit, None, parameters)

        if cliNode.GetStatus() & cliNode.ErrorsMask:
            raise ValueError("The image registration engine (BRAINSFit) failed.")

        #  Remuestrear la Dosis (BRAINSResample)
        output_dose_name = f"{moving_dose.GetName()}_Aligned"
        volumesLogic = slicer.modules.volumes.logic()

        # Clonamos el 'envase' de la Dosis Nueva (fixed_dose) para tener su tamaño exacto
        outputDose = volumesLogic.CloneVolume(slicer.mrmlScene, fixed_dose, output_dose_name)
        outputDose.SetAttribute("DICOM.Modality", "RTDOSE")

        resample_params = {
            "inputVolume": moving_dose.GetID(),
            "referenceVolume": fixed_dose.GetID(),
            "outputVolume": outputDose.GetID(),
            "warpTransform": transformNode.GetID(),
            "interpolationMode": "Linear",  # Interpolación lineal para dosis continuas
            "pixelType": "float"
        }

        brainsResample = slicer.modules.brainsresample
        cliNodeResample = slicer.cli.runSync(brainsResample, None, resample_params)

        if cliNodeResample.GetStatus() & cliNodeResample.ErrorsMask:
            raise ValueError("The Dose resample (BRAINSResample) failed.")

        # 1. Le aplicamos la matriz espacial calculada al CT Viejo
        moving_ct.SetAndObserveTransformNodeID(transformNode.GetID())
        # 2. Le decimos a Slicer que ponga el CT Nuevo de fondo, el Viejo encima, al 50% de transparencia
        slicer.util.setSliceViewerLayers(background=fixed_ct, foreground=moving_ct, foregroundOpacity=0.5)

        return outputDose

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
       # nuevo_nombre = f"RadComp_EQD2_Acumulado_ab{int(ab)}"

        # Aquí aplicamos la lógica del nombre
        if custom_name:
            nuevo_nombre = custom_name
        else:
            nuevo_nombre = f"RadComp_EQD2_Accumulated_ab{int(ab)}"

        eqd2_node = volumesLogic.CloneVolume(slicer.mrmlScene, dose_a_node, nuevo_nombre)
        eqd2_node.SetAttribute("DICOM.Modality", "RTDOSE")
        slicer.util.updateVolumeFromArray(eqd2_node, eqd2_total)

        # --- PASO E: AUTOMATIZACIÓN VISUAL (MAGIA UI) ---
        # 1. Encontrar la dosis máxima para escalar los colores automáticamente
        dosis_maxima = np.max(eqd2_total)

        # 2. Configurar el "Display Node" (el pintor de Slicer)
        display_node = eqd2_node.GetDisplayNode()
        if display_node is None:
            eqd2_node.CreateDefaultDisplayNodes()
            display_node = eqd2_node.GetDisplayNode()

        # 3. Aplicar paleta de colores de dosis (Arcoíris)
        #display_node.SetAndObserveColorNodeID('vtkMRMLColorTableNodeRainbow')
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
class SlicerRadCompTest(ScriptedLoadableModuleTest):
    def setUp(self):
        slicer.mrmlScene.Clear()

    def runTest(self):
        pass