from PyQt6.QtWidgets import QWidget, QFileDialog, QMessageBox
from app.ui.shot_generator_widget_ui import Ui_Form
from app.data.project import project_list
from app.services.file_manager import FileManager


class ShotGeneratorHandler(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.toolButton_csv.clicked.connect(lambda: self.on_select_file("csv", "Select CSV File"))
        self.ui.toolButton_blender.clicked.connect(lambda: self.on_select_file("blender", "Select Blender Program"))
        self.ui.toolButton_mastershot.clicked.connect(
            lambda: self.on_select_file("mastershot", "Select Mastershot File"))
        for project in project_list:
            self.ui.comboBox_project.addItem(project[1])

    def on_scan_files(self):
        project_data = next((p for p in project_list if p[1] == self.ui.comboBox_project.currentText()), None)
        if not project_data:
            QMessageBox.warning(self, "Error", "No project selected")
            return

        project_path = FileManager().get_project_path(project_data[0])

    def on_select_file(self, file_type: str, message: str):
        file_path, _ = QFileDialog.getOpenFileName(self, message, "", "All Files (*)")
        if file_path:
            if file_type == "csv":
                self.ui.lineEdit_csv.setText(file_path)
            elif file_type == "blender":
                self.ui.lineEdit_blender.setText(file_path)
            elif file_type == "mastershot":
                self.ui.lineEdit_mastershot.setText(file_path)
