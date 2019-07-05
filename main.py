import sys
from PyQt5.QtWidgets import QApplication, QFrame, QAction, QMainWindow, \
    QLabel, QFileDialog, QWidget, QVBoxLayout, QHBoxLayout, QProgressBar, \
    QMessageBox
from PyQt5.QtGui import QColor, QPalette, QImage, QPixmap
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
import GifInfo
import os


class CentralWidget(QWidget):
    def __init__(self, parent):
        super(CentralWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.down_field = QHBoxLayout()

        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setLineWidth(1)

        self.frames = QLabel('Frame: 0/0')
        self.frames.setMinimumSize(100, 20)
        self.down_field.addWidget(self.frames)

        self.down_field.addStretch(1)
        self.fps = QLabel('FPS: 0')
        self.fps.setMinimumSize(50, 20)
        self.down_field.addWidget(self.fps)

        self.down_field.addStretch(1)
        self.isPaused = QLabel('Pause')
        self.isPaused.setMinimumSize(50, 20)
        self.down_field.addWidget(self.isPaused)

        self.gif_layout = QHBoxLayout()
        self.gif_layout.addStretch(1)
        self.gif_layout.addWidget(parent.img)
        self.gif_layout.addWidget(parent.pbar)
        self.gif_layout.addStretch(1)

        self.layout.addStretch(1)
        self.layout.addLayout(self.gif_layout)
        self.layout.addStretch(1)
        self.layout.addWidget(self.separator)
        self.layout.addLayout(self.down_field)


class SomeThread(QThread):
    def __init__(self, fname, o):
        super().__init__()
        self.fname = fname
        self.o = o

    def run(self):
        try:
            gifinfo = GifInfo.GifInfo(self.fname, self.o)
            self.o.pbar.setValue(30)
            self.o.gifinfo = gifinfo
            self.o.frames = self.o.get_all_pixmaps()
            self.o.loaded_signal.emit()
        except KeyError:
            self.o.exception_signal.emit(Exception('Error: LZW decode'))
        except Exception as e:
            self.o.exception_signal.emit(e)


class Widget(QMainWindow):
    loaded_signal = pyqtSignal()
    progress_bar = pyqtSignal(int)
    exception_signal = pyqtSignal(Exception)

    def __init__(self):
        super().__init__()
        self.pbar = QProgressBar(self)
        self.pbar.setGeometry(30, 40, 200, 25)
        self.pbar.setValue(0)
        self.pbar.hide()
        self.isOpened = False
        self.is_loading = False
        self.img = QLabel()
        self.form_widget = CentralWidget(self)
        self.setCentralWidget(self.form_widget)

        self.progress_bar.connect(self.pbar.setValue)
        self.exception_signal.connect(self.show_error)
        self.loaded_signal.connect(self.set_gif_settings)

        self.gifinfo = None
        self.gif_id = 0

        self.create_menubar()

        self.scrTimer = QTimer(self)
        self.scrTimer.setInterval(50)
        self.scrTimer.timeout.connect(self.timerEvent)

        self.pal = self.form_widget.isPaused.palette()
        self.pal.setColor(QPalette.WindowText, QColor("red"))
        self.form_widget.isPaused.setPalette(self.pal)
        self.frames = [QPixmap()]

    def show_error(self, e):
        self.test = QMessageBox(self)
        self.test.setWindowModality(Qt.ApplicationModal)
        self.test.setWindowTitle('Error')
        self.test.setIcon(QMessageBox.Critical)
        self.test.setText(str(e))
        self.test.setStandardButtons(QMessageBox.Ok)
        self.test.show()
        self.pbar.hide()
        self.is_loading = False

    def create_menubar(self):
        main_menu = self.menuBar()

        file_menu = main_menu.addMenu('File')
        open_button = QAction('Open', self)
        open_button.setShortcut('Ctrl+O')
        open_button.triggered.connect(self.open_gif)
        close_button = QAction('Close', self)
        close_button.setShortcut('Ctrl+C')
        close_button.triggered.connect(self.close_gif)
        file_menu.addAction(open_button)
        file_menu.addAction(close_button)

        frame_menu = main_menu.addMenu('Frame')
        prev_button = QAction('Prev', self)
        prev_button.setShortcut('Left')
        prev_button.triggered.connect(self.prev_frame)
        pause_button = QAction('Play/Pause', self)
        pause_button.setShortcut('Space')
        pause_button.triggered.connect(self.pause_gif)
        next_button = QAction('Next', self)
        next_button.setShortcut('Right')
        next_button.triggered.connect(self.next_frame)
        frame_menu.addAction(prev_button)
        frame_menu.addAction(pause_button)
        frame_menu.addAction(next_button)

        play_menu = main_menu.addMenu('Play')
        dspeed_button = QAction('Speed -', self)
        dspeed_button.setShortcut('-')
        dspeed_button.triggered.connect(self.dspeed_gif)
        uspeed_button = QAction('Speed +', self)
        uspeed_button.setShortcut('+')
        uspeed_button.triggered.connect(self.uspeed_gif)
        play_menu.addAction(dspeed_button)
        play_menu.addAction(uspeed_button)

        return main_menu

    def open_gif(self):
        if self.is_loading:
            return
        self.is_loading = True
        self.fname = QFileDialog.getOpenFileName(
            self,
            'Open file',
            options=QFileDialog.DontUseNativeDialog)[0]
        if not self.fname:
            self.is_loading = False
            return
        self.close_gif()
        self.pbar.show()
        self.update()
        self.t = SomeThread(self.fname, self)
        self.t.start()

    def set_gif_settings(self):
        self.form_widget.isPaused.setText('Play')
        self.pal.setColor(QPalette.WindowText, QColor("green"))
        self.form_widget.isPaused.setPalette(self.pal)
        fps = round(1000 / self.scrTimer.interval())
        self.form_widget.fps.setText('FPS: {}'.format(fps))
        frames_length = len(self.gifinfo.frames)
        self.form_widget.frames.setText('Frame: 1/{}'.format(frames_length))
        self.isOpened = True
        width = int(self.gifinfo.width, 16)
        height = int(self.gifinfo.height, 16)
        width = width + 18 if width + 18 > 300 else 300
        height = height + 74 if height + 74 > 300 else 300
        self.setMinimumSize(width, height)
        self.resize(width, height)
        self.setWindowTitle(self.fname)
        self.pbar.hide()
        self.pbar.setValue(0)
        self.scrTimer.start()
        self.is_loading = False

    def close_gif(self):
        self.scrTimer.stop()
        self.gif_id = 0
        self.isOpened = False
        self.frames = [QPixmap(QImage().fill(QColor('#ffffff')))]
        self.form_widget.fps.setText('FPS: 0')
        self.form_widget.frames.setText('Frames: 0/0')
        self.form_widget.isPaused.setText('Pause')
        self.pal.setColor(QPalette.WindowText, QColor("red"))
        self.form_widget.isPaused.setPalette(self.pal)
        self.setMinimumSize(300, 300)
        self.resize(300, 300)
        self.setWindowTitle('GIF')
        self.update()

    def pause_gif(self):
        if not self.isOpened:
            return
        if self.scrTimer.isActive():
            self.scrTimer.stop()
        else:
            self.scrTimer.start()
        self.change_pause_text()

    def change_pause_text(self):
        if self.scrTimer.isActive():
            self.form_widget.isPaused.setText('Play')
            self.form_widget.isPaused.adjustSize()
            self.pal.setColor(QPalette.WindowText, QColor("green"))
            self.form_widget.isPaused.setPalette(self.pal)
        else:
            self.form_widget.isPaused.setText('Pause')
            self.form_widget.isPaused.adjustSize()
            self.pal.setColor(QPalette.WindowText, QColor("red"))
            self.form_widget.isPaused.setPalette(self.pal)

    def prev_frame(self):
        if not self.isOpened:
            return
        self.scrTimer.stop()
        if self.gif_id:
            self.gif_id -= 1
        else:
            self.gif_id = len(self.gifinfo.images) - 1
        self.set_frames_text()
        self.change_pause_text()
        self.update()

    def next_frame(self):
        if not self.isOpened:
            return
        self.scrTimer.stop()
        self.change_pause_text()
        if self.gif_id != len(self.gifinfo.frames) - 1:
            self.gif_id += 1
        else:
            self.gif_id = 0
        self.set_frames_text()
        self.update()

    def set_frames_text(self):
        frames_text = 'Frame: {}/{}'.format(self.gif_id + 1,
                                            len(self.gifinfo.frames))
        self.form_widget.frames.setText(frames_text)

    def set_fps_text(self):
        fps_text = 'FPS: {}'.format(round(1000 / self.scrTimer.interval()))
        self.form_widget.fps.setText(fps_text)

    def uspeed_gif(self):
        if not self.isOpened:
            return
        current_interval = self.scrTimer.interval()
        possible_fps = 1000 / current_interval + 1
        if possible_fps > 20:
            self.scrTimer.setInterval(50)
        else:
            self.scrTimer.setInterval(round(1000 / possible_fps))
        self.set_fps_text()

    def dspeed_gif(self):
        if not self.isOpened:
            return
        current_interval = self.scrTimer.interval()
        possible_fps = 1000 / current_interval - 1
        if possible_fps < 1:
            self.scrTimer.setInterval(1000)
        else:
            self.scrTimer.setInterval(round(1000 / possible_fps))
        self.set_fps_text()

    def timerEvent(self):
        self.gif_id = (self.gif_id + 1) % len(self.gifinfo.images)
        self.set_frames_text()
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        self.img.setPixmap(self.frames[self.gif_id])

    def get_all_pixmaps(self):
        result = []
        count = len(self.gifinfo.frames)
        all_percents = 70
        z = 0
        all = int(self.gifinfo.height, 16) * count
        for t in self.gifinfo.frames:
            frame = QImage(int(self.gifinfo.width, 16),
                           int(self.gifinfo.height, 16),
                           QImage.Format_RGB32)
            y = 0
            for i in t:
                x = 0
                for j in i:
                    frame.setPixelColor(x, y, QColor('#' + j))
                    x += 1
                y += 1

                z += 1
                self.progress_bar.emit(all_percents * z / all + 30)
            result.append(QPixmap(frame))
            self.progress_bar.emit(all_percents * z / all + 30)
        return result


if __name__ == '__main__':
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = 'auto'
    os.environ['QT_SCREEN_SCALE_FACTORS'] = 'auto'
    os.environ['QT_SCALE_FACTOR'] = 'auto'
    app = QApplication(sys.argv)
    w = Widget()
    w.setMinimumSize(300, 300)
    w.resize(300, 300)
    w.move(300, 300)
    w.setWindowTitle('GIF')
    w.show()
    sys.exit(app.exec_())
