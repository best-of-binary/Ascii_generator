#!/data/data/com.termux/files/usr/bin/bash
set -e
if [ ! -d "/data/data/com.termux/files/usr" ]; then
    echo "This script is designed for Termux on Android. Aborting."
    exit 1
fi

termux-setup-storage || true
NEED_INSTALL=0
for pkg in python ffmpeg; do
    command -v "$pkg" >/dev/null 2>&1 || NEED_INSTALL=1
done
python3 -c "import cv2, numpy" 2>/dev/null || NEED_INSTALL=1
command -v termux-storage-get >/dev/null 2>&1 || NEED_INSTALL=1

if [ "$NEED_INSTALL" -eq 1 ]; then
    echo "Installing dependencies..."
    pkg update -y
    pkg upgrade -y
    pkg install -y x11-repo
    pkg install -y python python-numpy opencv-python ffmpeg termux-api dbus
else
    echo "Dependencies already present, skipping install."
fi

python3 -c "import cv2, numpy; print('OpenCV ' + cv2.__version__ + ' & NumPy OK')"

echo "Setup complete."
