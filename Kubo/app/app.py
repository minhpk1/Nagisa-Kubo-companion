import argparse
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
import sounddevice as sd
from PySide6.QtCore import Qt, QTimer, QSettings, QUrl
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtGui import QColor, QIcon, QPixmap, QFont, QFontDatabase
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMenu, QSystemTrayIcon, QDialog, QFormLayout,
    QLineEdit, QTextEdit, QComboBox, QDialogButtonBox, QFileDialog, QMessageBox, QSlider, QCheckBox, QListWidget, QListWidgetItem)

import paths
from avatar import Avatar
from live_client import LiveWorker
from protocol import DEFAULT_PROMPT
from emotions import EMOTIONS, ConversationExpressions
from agent_tools import NOTEPAD, default_apps

ROOT = Path(__file__).resolve().parent
if (ROOT / '.env').is_file():
    load_dotenv(ROOT / '.env')
if (paths.get_user_data_dir() / '.env').is_file():
    load_dotenv(paths.get_user_data_dir() / '.env')


class Settings(QDialog):
    def __init__(self, owner):
        super().__init__(owner)
        self.setWindowTitle('Cài đặt Kubo')
        self.resize(450, 400)
        form = QFormLayout(self)
        self.key = QLineEdit(owner.api_key)
        self.key.setEchoMode(QLineEdit.EchoMode.Password)
        self.key.setPlaceholderText('OpenAI project API key (kept in memory)')
        self.voice = QComboBox()
        self.voice.addItems(['marin','quartz','gleam','willow','ripple','vesper','stone','meridian','bossa','tempo','beacon','delta','cinder'])
        self.voice.setCurrentText(owner.config['voice'])
        self.backend = QLineEdit(owner.config['backend'])
        self.prompt = QTextEdit(owner.config['instructions'])
        self.prompt.setMaximumHeight(90)
        self.inputs, self.outputs = QComboBox(), QComboBox()
        for box in (self.inputs, self.outputs):
            box.addItem('Mặc định hệ thống', None)
        try:
            for idx, device in enumerate(sd.query_devices()):
                for box, direction in ((self.inputs,'input'),(self.outputs,'output')):
                    if device[f'max_{direction}_channels'] > 0:
                        host = sd.query_hostapis(device['hostapi'])['name']
                        box.addItem(f"{device['name']} ({host})", idx)
        except sd.PortAudioError:
            pass
        for box, device in ((self.inputs,owner.input_device),(self.outputs,owner.output_device)):
            box.setCurrentIndex(max(0,box.findData(device)))
        form.addRow('API key',self.key)
        form.addRow('Giọng nền',self.voice)
        form.addRow(QLabel('Giọng phát: Nagisa Kubo · cao độ +6'))
        form.addRow('Mô hình hội thoại',self.backend)
        form.addRow('Micro',self.inputs)
        form.addRow('Loa',self.outputs)
        form.addRow('Tính cách',self.prompt)
        self.agent_enabled = QCheckBox('Cho Kubo mở ứng dụng, tìm/đọc, mở file/thư mục và phát WAV')
        self.agent_enabled.setChecked(owner.config.get('agent_enabled', True))
        form.addRow(self.agent_enabled)
        self.roots = QListWidget()
        self.roots.addItems(owner.allowed_roots)
        self.roots.setMaximumHeight(90)
        form.addRow('Thư mục được phép', self.roots)
        folders = QHBoxLayout()
        add = QPushButton('Thêm thư mục…')
        remove = QPushButton('Bỏ quyền thư mục')
        add.clicked.connect(self.add_root)
        remove.clicked.connect(lambda: self.roots.takeItem(self.roots.currentRow()) if self.roots.currentRow() >= 0 else None)
        folders.addWidget(add); folders.addWidget(remove)
        form.addRow(folders)
        self.apps = QListWidget()
        self.apps.setMaximumHeight(70)
        for application in owner.allowed_apps:
            self.append_app(application)
        form.addRow('Ứng dụng được phép', self.apps)
        apps_row = QHBoxLayout()
        add_app = QPushButton('Thêm ứng dụng (.exe)…')
        remove_app = QPushButton('Bỏ quyền ứng dụng')
        add_app.clicked.connect(self.add_app)
        remove_app.clicked.connect(lambda: self.apps.takeItem(self.apps.currentRow()) if self.apps.currentRow() >= 0 else None)
        apps_row.addWidget(add_app); apps_row.addWidget(remove_app)
        form.addRow(apps_row)
        self.editor = QLineEdit(owner.code_editor)
        self.editor.setReadOnly(True)
        editor_row = QHBoxLayout()
        editor_row.addWidget(self.editor)
        choose_editor = QPushButton('Chọn trình sửa code…')
        choose_editor.clicked.connect(self.choose_editor)
        editor_row.addWidget(choose_editor)
        form.addRow('Mở code bằng', editor_row)
        privacy = QLabel('File chỉ được đọc/mở trong các thư mục đã chọn; nội dung khi đọc sẽ gửi tới dịch vụ AI. Ứng dụng được cấp quyền riêng ở trên. Code mở bằng Notepad hoặc trình soạn thảo bạn chọn, không tự chạy/biên dịch. Kubo không có công cụ sửa/xóa file hay chạy lệnh tùy ý.')
        privacy.setWordWrap(True); form.addRow(privacy)
        hint = QLabel('Nên dùng tai nghe. Phiên trực tuyến có thể phát sinh phí.\nTắt micro không kết thúc phiên; chọn Ngắt kết nối để dừng.')
        form.addRow(hint)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def add_root(self):
        folder = QFileDialog.getExistingDirectory(self, 'Chọn thư mục cho phép Kubo đọc')
        if folder and folder not in [self.roots.item(i).text() for i in range(self.roots.count())]:
            self.roots.addItem(str(Path(folder).resolve()))

    def append_app(self, application):
        item = QListWidgetItem(application['name'])
        item.setData(Qt.ItemDataRole.UserRole, dict(application))
        item.setToolTip(application['path'])
        self.apps.addItem(item)

    def app_values(self):
        return [self.apps.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.apps.count())]

    def add_app(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Chọn ứng dụng được phép mở', '', 'Ứng dụng Windows (*.exe)')
        if filename:
            path = Path(filename).resolve()
            if path.suffix.lower() == '.exe' and not any(Path(a['path']) == path for a in self.app_values()):
                self.append_app({'name':path.stem, 'path':str(path)})

    def choose_editor(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Chọn trình soạn thảo: Code.exe, notepad.exe…', '', 'Trình soạn thảo Windows (*.exe)')
        if filename and Path(filename).suffix.lower() == '.exe':
            self.editor.setText(str(Path(filename).resolve()))


class Companion(QWidget):
    def __init__(self, demo=False):
        super().__init__()
        self.setWindowTitle('Kubo — AI desktop companion')
        self.preferences = QSettings('DesktopCompanion', 'Kubo')
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.api_key = os.getenv('OPENAI_API_KEY','')
        self.config = {'voice':os.getenv('LIVE_VOICE','marin'), 'instructions':DEFAULT_PROMPT,
                       'backend':os.getenv('BACKEND_MODEL','gpt-5.6-luna'),
                       'agent_enabled':self.preferences.value('agent_enabled',True,type=bool)}
        self.allowed_roots = self.preferences.value('allowed_roots', paths.get_default_allowed_roots(), type=list)
        try:
            self.allowed_apps = json.loads(self.preferences.value('allowed_apps', json.dumps(default_apps())))
            if not isinstance(self.allowed_apps, list) or any(not isinstance(a,dict) or
                    not isinstance(a.get('name'),str) or not isinstance(a.get('path'),str) for a in self.allowed_apps):
                raise ValueError('Invalid app settings')
        except (ValueError, TypeError):
            self.allowed_apps = default_apps()
        self.code_editor = self.preferences.value('code_editor', NOTEPAD)
        self.worker = None
        self.input_device = self.output_device = None
        self.connected_at = None
        self.exiting = False
        self.last_error = ''
        self.transcript_text = ''
        self.expressions = ConversationExpressions()
        self.last_speaker = ''
        self.setFixedWidth(360)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10,5,10,10); layout.setSpacing(5)
        self.bubble = QLabel('Chào bạn! Mình là Kubo!\nKết nối để trò chuyện cùng mình nhé.')
        self.bubble.setTextFormat(Qt.TextFormat.PlainText)
        self.bubble.setWordWrap(True)
        self.bubble.setMinimumHeight(64)
        self.bubble.setMaximumHeight(96)
        self.bubble.setStyleSheet('QLabel { background: #292336; color: #f7efff; border: 1px solid #bda0e0; border-radius: 16px; padding: 12px; font-size: 13px; }')
        layout.addWidget(self.bubble)
        self.avatar = Avatar(self)
        self.avatar.demo = demo
        self.avatar.load_images(paths.get_avatars_dir())

        layout.addWidget(self.avatar)
        panel = QWidget()
        panel.setObjectName('panel')
        panel.setStyleSheet('QWidget#panel {background:#292336; border:1px solid #bda0e0; border-radius:14px;} QLabel {color:#e9ddf7;} QPushButton {background:#514060;color:white;border:0;border-radius:8px;padding:8px;} QPushButton:hover {background:#735688;} QPushButton:disabled {color:#938b9f;} QPushButton:checked {background:#825eaa;} QComboBox {background:#514060;color:white;border:0;border-radius:6px;padding:6px;} QSlider::groove:horizontal {height:4px;background:#514060;} QSlider::handle:horizontal {background:#bda0e0;width:14px;margin:-5px 0;border-radius:7px;}')
        controls = QVBoxLayout(panel)
        title = QLabel('NAGISA KUBO  /  GIỌNG +6')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls.addWidget(title)
        self.sample = QSoundEffect(self)
        self.sample.setSource(QUrl.fromLocalFile(str(paths.get_samples_dir() / 'kubo-plus6.wav')))
        self.sample.setVolume(.7)
        self.sample.playingChanged.connect(self.sample_changed)
        self.sample_button = QPushButton('Nghe thử giọng Kubo +6')
        self.sample_button.clicked.connect(self.play_sample)
        controls.addWidget(self.sample_button)
        self.tool_player = QSoundEffect(self)
        self.tool_player.setVolume(.7)
        self.tool_request = None
        self.tool_player.statusChanged.connect(self.tool_player_status)
        self.tool_player.playingChanged.connect(self.tool_playing_changed)
        self.tool_label = QLabel('Công cụ: sẵn sàng' if self.config['agent_enabled'] else 'Công cụ: đã tắt')
        self.tool_label.setWordWrap(True)
        controls.addWidget(self.tool_label)
        self.stop_audio_button = QPushButton('Dừng audio đang phát')
        self.stop_audio_button.clicked.connect(self.stop_tool_audio)
        self.stop_audio_button.setVisible(False)
        controls.addWidget(self.stop_audio_button)
        self.emotion_box = QComboBox()
        self.emotion_box.addItem('Tự động theo hội thoại', 'auto')
        for key, label in EMOTIONS.items(): self.emotion_box.addItem(label, key)
        self.emotion_box.setCurrentIndex(max(0, self.emotion_box.findData(self.preferences.value('emotion', 'auto'))))
        self.emotion_box.setToolTip('Phản ứng theo cụm từ trong lời bạn và Kubo; giữ biểu cảm qua các đoạn lời nói. Không phân tích cảm xúc âm thanh.')
        controls.addWidget(self.emotion_box)
        self.emotion_label = QLabel()
        controls.addWidget(self.emotion_label)
        customization = QHBoxLayout()
        color_button = QPushButton('Mặc định')
        color_button.clicked.connect(lambda: self.avatar.load_images(paths.get_avatars_dir()))
        customization.addWidget(color_button)
        customization.addWidget(QLabel('Chuyển động'))
        self.intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.intensity_slider.setRange(0,100)
        self.intensity_slider.setValue(int(self.preferences.value('intensity',80)))
        self.avatar.intensity = self.intensity_slider.value()/100
        self.intensity_slider.setToolTip('Điều chỉnh độ chuyển động nhẹ của nhân vật; kéo về 0 để đứng yên.')
        self.intensity_slider.valueChanged.connect(self.change_intensity)
        customization.addWidget(self.intensity_slider)
        controls.addLayout(customization)
        self.emotion_box.currentIndexChanged.connect(self.update_emotion)
        self.update_emotion()
        self.status = QLabel('CHƯA KẾT NỐI · micro tắt' if not demo else 'XEM THỬ · micro tắt')
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls.addWidget(self.status)
        row = QHBoxLayout()
        self.connect_button = QPushButton('Kết nối')
        self.connect_button.clicked.connect(self.toggle_connection)
        self.mute_button = QPushButton('Tắt micro')
        self.mute_button.setCheckable(True); self.mute_button.setEnabled(False)
        self.mute_button.toggled.connect(self.set_muted)
        menu_button = QPushButton('•••'); menu_button.setFixedWidth(40)
        menu_button.clicked.connect(lambda: self.menu.exec(menu_button.mapToGlobal(menu_button.rect().bottomLeft())))
        for button in (self.connect_button,self.mute_button,menu_button): row.addWidget(button)
        controls.addLayout(row)
        layout.addWidget(panel)
        self.menu = QMenu(self)
        self.settings_action = self.menu.addAction('Cài đặt…',self.settings)
        self.menu.addAction('Chọn bộ ảnh khác…',self.choose_avatar)
        self.menu.addAction('Dùng nhân vật Kubo mặc định',lambda: self.avatar.load_images(paths.get_avatars_dir()))
        self.menu.addAction('Xem thử chuyển động nói',self.toggle_demo)
        self.menu.addAction('Nguồn giọng & Credit…', self.show_voice_credits)
        self.menu.addSeparator()
        self.menu.addAction('Ẩn / hiện',self.toggle_visibility)
        self.menu.addAction('Thoát',self.close)

        icon = QPixmap(32,32); icon.fill(QColor('#bda0e0'))
        self.tray = QSystemTrayIcon(QIcon(icon),self)
        self.tray.setToolTip('Kubo · AI desktop companion')
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.tray_activated)
        self.tray.show()
        self.timer = QTimer(self); self.timer.timeout.connect(self.tick); self.timer.start(33)
        self.adjustSize()
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right()-self.width()-24,screen.bottom()-self.height()-24)

    def contextMenuEvent(self,event):
        self.menu.exec(event.globalPos())

    def show_voice_credits(self):
        text = (
            "NAGISA KUBO - NGUỒN GIỌNG & CREDIT\n\n"
            "Dự án sử dụng pack giọng:\n"
            "Nagisa Kubo (Kubo Won't Let Me Be Invisible) (JP) (RVC V2 300 Epochs)\n\n"
            "• Tác giả ghi trong bài đăng nguồn: Discord ID 416975678542446592 (<@416975678542446592>)\n"
            "• Nguồn lưu trữ: https://huggingface.co/Kuma6/Nagisa-Kubo\n"
            "• Thiết lập cao độ: +6 (cấu hình chuyển giọng trong ứng dụng)\n\n"
            "Dự án Kubo Desktop tích hợp mô hình có sẵn này và không tự nhận đã train mô hình gốc.\n"
            "Chi tiết xem tại CREDITS.md."
        )
        QMessageBox.information(self, 'Nguồn giọng & Credit — Nagisa Kubo', text)


    def finish_tool_request(self, result):
        request, self.tool_request = self.tool_request, None
        if request:
            request['result'] = result
            request['done'].set()

    def stop_tool_audio(self):
        self.finish_tool_request({'ok':False,'error':'Phát audio đã hủy.'})
        self.tool_player.stop()

    def on_tool_ui(self, request):
        if request['cancelled'].is_set() or not self.worker or self.worker.stop_event.is_set():
            request['result']={'ok':False,'error':'Phiên đã dừng.'};request['done'].set();return
        self.stop_tool_audio()
        self.sample.stop()
        self.tool_request=request
        if request['action']=='stop_audio':
            self.finish_tool_request({'ok':True,'status':'stopped'})
            return
        self.tool_player.setSource(QUrl.fromLocalFile(request['path']))
        self.tool_player_status()

    def tool_player_status(self):
        if not self.tool_request: return
        if self.tool_request['cancelled'].is_set():
            self.stop_tool_audio();return
        if self.tool_player.status()==QSoundEffect.Status.Ready:
            self.tool_player.play()
        elif self.tool_player.status()==QSoundEffect.Status.Error:
            self.finish_tool_request({'ok':False,'error':'Không giải mã/phát được WAV.'})

    def tool_playing_changed(self):
        playing=self.tool_player.isPlaying()
        self.stop_audio_button.setVisible(playing)
        if self.worker:
            if playing: self.worker.audio.suppress_output.set()
            else: self.worker.audio.suppress_output.clear()
        if playing:
            if self.tool_request and self.tool_request['cancelled'].is_set():
                self.stop_tool_audio();return
            self.finish_tool_request({'ok':True,'status':'playback_started'})
        self.adjustSize()

    def on_tool_status(self, text):
        labels={'list_roots':'xem phạm vi truy cập','list_folder':'liệt kê thư mục',
                'find_files':'tìm file','read_text':'đọc văn bản','open_folder':'mở thư mục','open_file':'mở file',
                'play_audio':'phát audio','stop_audio':'dừng audio',
                'list_apps':'liệt kê ứng dụng','open_app':'mở ứng dụng'}
        for name,label in labels.items(): text=text.replace(name,label)
        self.tool_label.setText(text)

    def play_sample(self):
        if self.worker:
            return
        sample_file = paths.get_samples_dir() / 'kubo-plus6.wav'
        if not sample_file.is_file():
            QMessageBox.warning(self, 'Nghe thử', f'Chưa có file mẫu giọng tại:\n{sample_file}\n\nXem hướng dẫn bổ sung dữ liệu trong docs/ASSETS.md.')
            return
        if self.sample.isPlaying():
            self.sample.stop()
        elif self.sample.status() == QSoundEffect.Status.Error:
            QMessageBox.warning(self, 'Nghe thử', 'Không phát được mẫu giọng. Kiểm tra loa và file assets/kubo-plus6.wav.')
        else:
            self.sample.play()

    def sample_changed(self):
        playing = self.sample.isPlaying()
        self.sample_button.setText('Dừng nghe thử' if playing else 'Nghe thử giọng Kubo +6')
        self.avatar.demo = playing

    def update_emotion(self, *_):
        mode = self.emotion_box.currentData()
        self.avatar.emotion = self.expressions.current() if mode == 'auto' else mode
        self.emotion_label.setText('Cảm xúc: ' + EMOTIONS[self.avatar.emotion])
        self.preferences.setValue('emotion', mode)
        self.avatar.update()

    def change_intensity(self, value):
        self.avatar.intensity = value / 100
        self.preferences.setValue('intensity', value)
        self.avatar.update()

    def toggle_visibility(self):
        if self.isVisible(): self.hide()
        else: self.show(); self.raise_()

    def tray_activated(self,reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick: self.toggle_visibility()

    def toggle_demo(self):
        if not self.worker: self.avatar.demo = not self.avatar.demo

    def choose_avatar(self):
        folder = QFileDialog.getExistingDirectory(self,'Choose folder with idle.png, talk.png, blink.png')
        if folder:
            if not self.avatar.load_images(folder):
                QMessageBox.information(self,'Avatar images','Không tìm thấy bộ ảnh hợp lệ. Giữ nguyên nhân vật hiện tại.')

    def settings(self):
        if self.worker: return
        dialog = Settings(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.api_key = dialog.key.text().strip()
            self.config = {'voice':dialog.voice.currentText(),
                           'backend':dialog.backend.text().strip() or 'gpt-5.6-luna',
                           'instructions':dialog.prompt.toPlainText().strip() or DEFAULT_PROMPT,
                           'agent_enabled':dialog.agent_enabled.isChecked()}
            self.allowed_roots=[dialog.roots.item(i).text() for i in range(dialog.roots.count())]
            self.preferences.setValue('allowed_roots',self.allowed_roots)
            self.allowed_apps = dialog.app_values()
            self.code_editor = dialog.editor.text()
            self.preferences.setValue('allowed_apps',json.dumps(self.allowed_apps,ensure_ascii=False))
            self.preferences.setValue('code_editor',self.code_editor)
            self.preferences.setValue('agent_enabled',self.config['agent_enabled'])
            self.tool_label.setText('Công cụ: sẵn sàng' if self.config['agent_enabled'] else 'Công cụ: đã tắt')
            self.input_device = dialog.inputs.currentData()
            self.output_device = dialog.outputs.currentData()

    def toggle_connection(self):
        if self.worker:
            self.stop_tool_audio()
            self.connect_button.setEnabled(False)
            self.status.setText('ĐANG NGẮT · micro tắt')
            self.worker.stop()
            return
        if not self.api_key:
            self.settings()
            if not self.api_key: return
        self.last_error = ''
        self.sample.stop()
        self.sample_button.setEnabled(False)
        self.avatar.demo = False
        self.transcript_text = ''; self.last_speaker = ''
        self.expressions.reset()
        self.update_emotion()
        self.status.setText('ĐANG KẾT NỐI · micro tắt')
        self.bubble.setText('Đang chuẩn bị giọng Kubo… Micro sẽ mở khi kết nối sẵn sàng.')
        self.connect_button.setText('Ngắt kết nối')
        self.settings_action.setEnabled(False)
        self.worker = LiveWorker(self.api_key,dict(self.config),self.input_device,self.output_device,
                                 roots=list(self.allowed_roots),apps=list(self.allowed_apps),editor=self.code_editor)
        self.worker.tool_status.connect(self.on_tool_status)
        self.worker.tool_ui.connect(self.on_tool_ui)
        self.worker.state.connect(self.on_state)
        self.worker.transcript.connect(self.on_transcript)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_state(self,state):
        self.status.setText(state)
        if state == 'Connected':
            self.connected_at = time.monotonic()
            self.mute_button.setEnabled(True)
            self.bubble.setText('Mình đang nghe đây. Bạn muốn trò chuyện gì nào?')
        elif state == 'Closing':
            self.connected_at = None
            self.mute_button.setEnabled(False)
            self.status.setText('ĐANG NGẮT · micro tắt')

    def on_transcript(self,speaker,delta):
        self.expressions.feed(speaker, delta)
        if speaker != self.last_speaker:
            self.transcript_text = ''; self.last_speaker = speaker
        self.transcript_text = (self.transcript_text + delta)[-240:]
        self.bubble.setText(f'{speaker}: {self.transcript_text}')
        self.update_emotion()

    def on_error(self,message):
        self.last_error = message
        self.bubble.setText('Kết nối đã dừng. Bạn có thể kết nối lại.')
        QMessageBox.warning(self,'Kết nối Kubo',message)

    def on_finished(self):
        self.stop_tool_audio()
        self.worker.deleteLater(); self.worker = None
        self.connected_at = None
        self.avatar.level = 0
        self.connect_button.setText('Kết nối'); self.connect_button.setEnabled(True)
        self.mute_button.setChecked(False); self.mute_button.setEnabled(False)
        self.settings_action.setEnabled(True)
        self.sample_button.setEnabled(True)
        self.status.setText('CHƯA KẾT NỐI · micro tắt')
        if not self.last_error: self.bubble.setText('Mình vẫn ở đây. Kết nối khi bạn muốn trò chuyện nhé.')
        if self.exiting: QApplication.quit()

    def set_muted(self,muted):
        self.mute_button.setText('Bật micro' if muted else 'Tắt micro')
        if self.worker: self.worker.mute(muted)

    def tick(self):
        if self.tool_request and self.tool_request['cancelled'].is_set():
            self.stop_tool_audio()
        if self.emotion_box.currentData() == 'auto':
            emotion = self.expressions.current()
            if self.avatar.emotion != emotion:
                self.avatar.emotion = emotion
                self.emotion_label.setText('Cảm xúc: ' + EMOTIONS[emotion])
                self.avatar.update()
        if self.worker:
            self.avatar.level = self.worker.audio.level
        if self.connected_at:
            seconds = int(time.monotonic()-self.connected_at)
            state = 'MICRO TẮT' if self.mute_button.isChecked() else 'ĐANG NGHE'
            self.status.setText(f'{state} · {seconds//60:02d}:{seconds%60:02d} · Kubo +6')

    def closeEvent(self,event):
        self.stop_tool_audio()
        self.sample.stop()
        if self.worker:
            event.ignore()
            self.exiting = True
            self.worker.stop()
            self.connect_button.setEnabled(False)
            self.status.setText('ĐANG NGẮT · micro tắt')
        else:
            self.tray.hide()
            event.accept()
            QApplication.quit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo',action='store_true',help='Animate the avatar without microphone or API use.')
    parser.add_argument('--screenshot',help=argparse.SUPPRESS)
    args = parser.parse_args()
    app = QApplication(sys.argv)
    font_file = Path(os.getenv('WINDIR', 'C:/Windows')) / 'Fonts' / 'segoeui.ttf'
    if font_file.exists():
        QFontDatabase.addApplicationFont(str(font_file))
    app.setFont(QFont('Segoe UI', 10))
    app.setQuitOnLastWindowClosed(False)
    app.setStyle('Fusion')
    window = Companion(args.demo)
    window.show()
    if args.screenshot:
        def capture():
            window.grab().save(args.screenshot)
            window.close()
        QTimer.singleShot(500,capture)
    sys.exit(app.exec())


if __name__ == '__main__':
    main()







