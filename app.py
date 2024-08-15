import sys
import os
import shutil
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QFileDialog, QMessageBox, QInputDialog

class SyncApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.label = QLabel('MP3 Sync Program', self)
        layout.addWidget(self.label)

        # Buttons for ripping to Folder A or B
        self.rip_button_a = QPushButton('Rip CD to Folder A', self)
        self.rip_button_a.clicked.connect(lambda: self.rip_cd_to_folder("FolderA"))
        layout.addWidget(self.rip_button_a)

        self.rip_button_b = QPushButton('Rip CD to Folder B', self)
        self.rip_button_b.clicked.connect(lambda: self.rip_cd_to_folder("FolderB"))
        layout.addWidget(self.rip_button_b)

        # Button for syncing either folder to the MP3 player
        self.sync_button = QPushButton('Sync Folder to Device', self)
        self.sync_button.clicked.connect(self.sync_device)
        layout.addWidget(self.sync_button)

        self.setLayout(layout)
        self.setWindowTitle('MP3 Sync Program')
        self.show()

    def get_cd_drive_selection(self):
        """
        Presents a dialog to the user to select the mounted CD drive.
        """
        volumes = [volume for volume in os.listdir('/Volumes') if os.path.ismount(os.path.join('/Volumes', volume))]
        if not volumes:
            QMessageBox.critical(self, "Error", "No mounted volumes detected!")
            return None

        # Ask the user to select the mounted drive (potential CD drive)
        cd_drive, ok = QInputDialog.getItem(self, "Select CD Drive", "Choose the CD drive:", volumes, 0, False)

        if ok and cd_drive:
            return os.path.join('/Volumes', cd_drive)
        else:
            return None

    def rip_cd_to_folder(self, folder_name):
        """
        Rips the CD to the specified folder (FolderA or FolderB).
        If abcde fails, attempts a simple file copy from the CD.
        """
        if not self.check_dependencies():
            return

        output_dir = os.path.expanduser(f"~/Desktop/DeviceSync/{folder_name}")
        os.makedirs(output_dir, exist_ok=True)

        # Ask user to select the CD drive
        cd_mount_point = self.get_cd_drive_selection()
        if not cd_mount_point:
            QMessageBox.critical(self, "Error", "No CD selected!")
            return

        # Attempt to run abcde to rip the CD from the selected drive
        try:
            subprocess.run(["abcde", "-d", cd_mount_point, "-o", "mp3", "-N", "-D", output_dir], check=True)
            QMessageBox.information(self, "Success", f"CD ripped successfully to {output_dir}!")
        except subprocess.CalledProcessError as e:
            # Log the error but proceed with file copying
            print(f"abcde failed with error: {e}. Proceeding with file copy.")
            self.copy_files_from_cd(cd_mount_point, output_dir)

    def copy_files_from_cd(self, cd_mount_point, output_dir):
        """
        Copies files directly from the CD to the target folder.
        """
        try:
            # Copy files from the CD to the target folder
            for item in os.listdir(cd_mount_point):
                source_item = os.path.join(cd_mount_point, item)
                target_item = os.path.join(output_dir, item)
                if os.path.isdir(source_item):
                    shutil.copytree(source_item, target_item)
                else:
                    shutil.copy2(source_item, target_item)
            QMessageBox.information(self, "Success", f"Files copied from CD to {output_dir}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy files from CD: {e}")

    def sync_device(self):
        """
        Sync files from either Folder A or Folder B to the connected MP3 player.
        """
        # Present a dropdown to select between Folder A or Folder B
        items = ["Folder A", "Folder B"]
        folder_choice, ok = QInputDialog.getItem(self, "Select Folder", "Choose which folder to sync:", items, 0, False)

        if not ok:
            return  # User canceled the selection

        # Set the appropriate folder based on the user's selection
        if folder_choice == "Folder A":
            source_folder = os.path.expanduser("~/Desktop/DeviceSync/FolderA")
        else:
            source_folder = os.path.expanduser("~/Desktop/DeviceSync/FolderB")

        # Ensure the folder exists
        if not os.path.exists(source_folder):
            QMessageBox.critical(self, "Error", f"{source_folder} does not exist!")
            return

        # Detect MP3 player
        device_mount_point = self.detect_mp3_player()

        if not device_mount_point:
            QMessageBox.warning(self, "Warning", "No MP3 player detected or selected.")
            return

        # Sync files from the selected folder to the MP3 player
        try:
            for file_name in os.listdir(source_folder):
                full_file_name = os.path.join(source_folder, file_name)
                if os.path.isfile(full_file_name):
                    shutil.copy(full_file_name, device_mount_point)
            QMessageBox.information(self, "Success", f"Files synced successfully to {device_mount_point}!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to sync to device: {e}")

    def detect_mp3_player(self):
        """
        Detects a connected MP3 player by looking for typical volume labels or structure.
        If no player is found, it prompts the user to manually select the device.
        """
        # Try to detect by known labels or structure
        device_mount_point = self.detect_mp3_player_by_label() or self.detect_mp3_player_by_structure()

        if device_mount_point:
            return device_mount_point

        # Fallback to manual selection
        device_mount_point = QFileDialog.getExistingDirectory(self, "Select Device Mount Point")
        if device_mount_point:
            return device_mount_point

        return None

    def detect_mp3_player_by_label(self):
        """
        Detect MP3 player by known volume labels.
        """
        known_labels = ['MP3PLAYER', 'SANSA_CLIP', 'MP3 Device']

        for volume in os.listdir('/Volumes'):
            volume_path = os.path.join('/Volumes', volume)
            if os.path.ismount(volume_path) and volume in known_labels:
                print(f"MP3 player detected by label: {volume}")
                return volume_path
        return None

    def detect_mp3_player_by_structure(self):
        """
        Detect MP3 player by typical folder structure (e.g., /MUSIC/).
        """
        for volume in os.listdir('/Volumes'):
            volume_path = os.path.join('/Volumes', volume)
            if os.path.ismount(volume_path):
                if os.path.exists(os.path.join(volume_path, 'MUSIC')):
                    print(f"MP3 player detected by structure at {volume_path}")
                    return volume_path
        return None

    def check_dependencies(self):
        """
        Check if abcde is installed on the system.
        """
        if not shutil.which("abcde"):
            QMessageBox.critical(self, "Error", "abcde is not installed. Please install abcde and try again.")
            return False
        return True


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SyncApp()
    sys.exit(app.exec_())
