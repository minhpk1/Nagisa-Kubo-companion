"""Anime portrait renderer using the bundled Nagisa Kubo expression atlas."""
import math
import time
from pathlib import Path
from PySide6.QtCore import Qt, QRectF, QTimer
from PySide6.QtGui import QPainter, QPixmap, QPainterPath, QColor
from PySide6.QtWidgets import QWidget

ASSETS = Path(__file__).resolve().parent / 'assets'
STATES = ('idle', 'happy', 'sad', 'angry', 'shy', 'surprised', 'talk', 'blink', 'rest')

class Avatar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(340, 360)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.level = 0.0
        self.demo = False
        self.emotion = 'neutral'
        self.intensity = .8
        self.drag_offset = None
        self.images = {}
        self.setToolTip('Kéo Kubo để di chuyển. Nhấp chuột phải để mở menu.')
        self.load_images(ASSETS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(33)

    def load_images(self, folder):
        """An invalid custom folder preserves the current avatar."""
        folder = Path(folder)
        images = {}
        atlas = QPixmap(str(folder / 'kubo-atlas.png'))
        if not atlas.isNull():
            for index, name in enumerate(STATES):
                col, row = index % 3, index // 3
                left, top = round(col*atlas.width()/3), round(row*atlas.height()/3)
                right, bottom = round((col+1)*atlas.width()/3), round((row+1)*atlas.height()/3)
                images[name] = atlas.copy(left, top, right-left, bottom-top)
        for name in STATES:
            file = folder / f'{name}.png'
            if file.is_file():
                pixmap = QPixmap(str(file))
                if not pixmap.isNull(): images[name] = pixmap
        if 'idle' not in images: return False
        self.images = images
        self.update()
        return True

    def frame_name(self, t, level):
        emotion = self.emotion if self.emotion in self.images else 'idle'
        # Preserve selected expressions; neutral has dedicated animation frames.
        if emotion != 'idle': return emotion
        if level > .09 and int(t*8) % 2 == 0 and 'talk' in self.images: return 'talk'
        if t % 4.7 > 4.52 and 'blink' in self.images: return 'blink'
        return 'idle'

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = event.globalPosition().toPoint() - self.window().pos()

    def mouseMoveEvent(self, event):
        if self.drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self.drag_offset)

    def mouseReleaseEvent(self, event):
        self.drag_offset = None

    def paintEvent(self, event):
        p = QPainter(self)
        if not self.images:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect = QRectF(10, 10, self.width() - 20, self.height() - 20)
            p.fillRect(rect, QColor(40, 30, 60, 220))
            p.setPen(QColor('#e9ddf7'))
            font = p.font()
            font.setPointSize(9)
            p.setFont(font)
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, "Chưa có ảnh nhân vật\n(assets/kubo-atlas.png)\n\nXem docs/ASSETS.md")
            return
        t = time.monotonic()
        level = max(0, math.sin(t*14))*.7 if self.demo else self.level
        pixmap = self.images[self.frame_name(t, level)]
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        size = pixmap.size().scaled(336, 344, Qt.AspectRatioMode.KeepAspectRatio)
        bob = math.sin(t*1.8)*3*self.intensity
        rect = QRectF((self.width()-size.width())/2, 10+bob, size.width(), size.height())
        clip = QPainterPath()
        clip.addRoundedRect(rect, 18, 18)
        p.setClipPath(clip)
        p.drawPixmap(rect, pixmap, QRectF(pixmap.rect()))
