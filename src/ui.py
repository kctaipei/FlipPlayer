import ipywidgets as widgets
import cv2
from IPython.display import display

class UI:
    def __init__(self, player):
        self.player = player
        self.video_widget = widgets.Image(format = 'jpg', layout = widgets.Layout(width = '360px'))
        self.btn_pause = widgets.Button(description = '⏸')
        self.btn_record = widgets.Button(description = '⏺')
        self.btn_forward = widgets.Button(description = '▶')
        self.btn_backward = widgets.Button(description = '◀')
        self.btns = widgets.HBox([self.btn_backward, self.btn_pause, self.btn_forward, self.btn_record],\
            layout = widgets.Layout(width = '360px'))
        self.slider = widgets.IntSlider(value = 0, min = 0, max = player.total_frames - 1,\
            description = 'Frame', layout = widgets.Layout(width = '270px'))
        self.label = widgets.Label(value = str(player.play_state), layout = widgets.Layout(width = '90px'))
        
        self.btn_pause.on_click(self._set_pause)
        self.btn_record.on_click(self._set_record)
        self.btn_forward.on_click(self._set_forward)
        self.btn_backward.on_click(self._set_backward)
        self.slider.observe(self._on_slider_change)
        self.player.set_display_callback(self.display_frame)
        self.player.set_slider_callback(self.update_slider)

    def display_frame(self, frame):
        _, img = cv2.imencode('.jpg', frame)
        
        self.video_widget.value = img.tobytes()

    def update_slider(self, value):
        self.slider.value = value

    def display(self):
        display(widgets.VBox([self.video_widget, self.btns, widgets.HBox([self.label, self.slider])]))

    def _set_pause(self, button):
        self.player.pause()
        self.label.value = str(self.player.play_state)

    def _set_record(self, button):
        if self.player.record():
            self.btn_record.description = '⏹'
        else:
            for i in self.btns.children:
                i.disabled = True
            self.slider.disabled = True
        self.label.value = str(self.player.play_state)

    def _set_forward(self, button):
        self.player.play_forward()
        self.label.value = str(self.player.play_state)

    def _set_backward(self, button):
        self.player.play_backward()
        self.label.value = str(self.player.play_state)

    def _on_slider_change(self, change):
        if change['name'] == 'value':
            self.player.seek_frame(change['new'])