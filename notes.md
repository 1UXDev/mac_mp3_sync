# pip installs

pip install PyQt5 // build GUI
pip install pydub // manipulate / convert audio
brew install abcde lame // cd data and metadata

<!-- ------------------- -->

<!-- Emualte Test CD -->

hdiutil makehybrid -o ~/Desktop/my_cd.iso ~/Desktop/testfiles -iso -joliet

# Package python app

## Activate venv

source venv/bin/activate

## Package

pip install pyinstaller

pyinstaller --onefile --windowed --icon=icon.iconset/icon.icns app.py
