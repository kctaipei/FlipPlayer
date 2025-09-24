from enum import IntFlag
import av
import cv2
import threading
#import subprocess
import time
import os

class Player:
    class State(IntFlag):
        '''
        bit0: pause/play
        bit1: not record/record
        bit2: forward/backward
        '''
        STOP            = -1
        PAUSE           = 0b000
        RECORD          = 0b010
        PLAY_FORWARD    = 0b001
        PLAY_BACKWARD   = 0b101
        RECORD_FORWARD  = 0b011
        RECORD_BACKWARD = 0b111
        
        def __str__(self):
            mapping = {
                Player.State.STOP: '已停止',
                Player.State.PAUSE: '暫停中',
                Player.State.RECORD: '錄製中',
                Player.State.PLAY_FORWARD: '正播中',
                Player.State.PLAY_BACKWARD: '倒放中',
                Player.State.RECORD_FORWARD: '正播&錄製中',
                Player.State.RECORD_BACKWARD: '倒放&錄製中'
            }
            
            if self in mapping:
                return mapping[self]
            if not self & Player.State.PLAY_FORWARD:
                return mapping[Player.State.PAUSE]
            return str(int(self))

    def __init__(self, video_path):
        self.video_path = video_path
        self.container = av.open(video_path)
        self.stream = self.container.streams.video[0]
        #self.frame_info = self._get_frame_info()
        self.frame_info = [(i.pict_type.name, i.pts) for i in self.container.decode(self.stream)]
        self.durations = [self.frame_info[i][1] - self.frame_info[i - 1][1] for i in range(1, len(self.frame_info))]
        self.total_frames = int(cv2.VideoCapture(video_path).get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame = 0
        self.play_state = Player.State.PAUSE
        self.ignore_slider_change = False #slider is changed by user
        self.record_frames = []
        self.display_callback = None
        self.slider_callback = None
        self.thread = threading.Thread(target = self._play_video, daemon = True)

    def set_display_callback(self, func):
        self.display_callback = func

    def set_slider_callback(self, func):
        self.slider_callback = func

    def pause(self):
        self.play_state &= ~Player.State.PLAY_FORWARD

    def record(self):
        if self.play_state & Player.State.RECORD:
            self.play_state = Player.State.STOP
            return False
        self.play_state |= Player.State.RECORD
        return True

    def play_forward(self):
        self.play_state = self.play_state & ~0b100 | Player.State.PLAY_FORWARD

    def play_backward(self):
        self.play_state |= Player.State.PLAY_BACKWARD

    def seek_frame(self, frame):
        if self.ignore_slider_change:
            self.ignore_slider_change = False
            return
        self.current_frame = frame

    def start(self):
        self.thread.start()

    def _display_frame(self, frame):
        if self.display_callback:
            self.display_callback(frame)

    def _update_slider(self, value):
        if self.slider_callback:
            self.slider_callback(value)

    '''
    def _get_frame_info(self):
        # output: list(tuple(pict_type, pkt_pts))
        cmd = ['ffprobe', '-select_streams', 'v', '-show_frames', '-show_entries',\
               'frame=pict_type,pkt_pts', '-of', 'csv', self.video_path]
        ret = subprocess.run(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE, text = True)
        lines = ret.stdout.splitlines()
        frame_info = []
        
        for i in lines:
            split = i.split(',')
            
            frame_info.append((split[2], float(split[1])))
        return frame_info
    '''

    def _find_previous_i_frame(self, index):
        for i in reversed([i for i, info in enumerate(self.frame_info) if info[0] == 'I']):
            if i <= index:
                return i
        return 0

    def _is_play_backward(self, target):
        return target == self.current_frame and (self.play_state & Player.State.PLAY_BACKWARD == Player.State.PLAY_BACKWARD)\
            and self.play_state != Player.State.STOP

    def _reencode_video(self, output_path):
        if not self.record_frames:
            return
        
        container_out = av.open(output_path, mode = 'w')
        stream_out = container_out.add_stream(self.stream.codec.name, width = self.stream.width, height = self.stream.height,\
            time_base = self.stream.time_base, pix_fmt = 'yuv420p') # ensure compatibility
        idx_range = [0, self.total_frames]
        cap = cv2.VideoCapture(self.video_path)
        frames = []
        pts = 0
        
        for i in self.record_frames:
            idx_range[0] = min(i, idx_range[0])
            idx_range[1] = max(i, idx_range[1])
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx_range[0])
        for i in range(idx_range[1] - idx_range[0]):
            ret, frame = cap.read()
            
            if not ret:
                break
            frames.append(frame)
        cap.release()
        for i, idx in enumerate(self.record_frames):
            if idx < 0 or idx >= len(self.frame_info):
                continue
            
            frame = av.VideoFrame.from_ndarray(cv2.cvtColor(frames[idx - idx_range[0]], cv2.COLOR_BGR2RGB), format = 'rgb24')
            
            frame.pts = pts
            if i < len(self.record_frames) - 1:
                pts += self.durations[idx] if idx <= self.record_frames[i + 1] else self.durations[self.record_frames[i + 1]]
            for j in stream_out.encode(frame):
                container_out.mux(j)
        for i in stream_out.encode():
            container_out.mux(i)
        container_out.close()
        print(f'output: {output_path}')

    def _play_video(self):
        cap = cv2.VideoCapture(self.video_path)
        last_time = time.time()
        
        while True:
            if self.play_state == Player.State.STOP:
                break
            elif self.play_state & Player.State.PLAY_FORWARD == Player.State.PAUSE:
                time.sleep(.1)
            elif self.play_state & Player.State.PLAY_BACKWARD == Player.State.PLAY_FORWARD:
                if self.current_frame >= self.total_frames - 1:
                    self.current_frame = self.total_frames - 1
                    self.play_state &= ~Player.State.PLAY_FORWARD
                    continue
                cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
                
                ret, frame = cap.read()
                
                if not ret:
                    break
                self._display_frame(frame)
                if self.play_state & Player.State.RECORD:
                    self.record_frames.append(self.current_frame)
                self._update_slider(self.current_frame + 1)
                if self.current_frame < self.total_frames - 1:
                    time.sleep(max(float(self.durations[self.current_frame] * self.stream.time_base) - time.time() + last_time, .0))
                    last_time = time.time()
            elif self.play_state & Player.State.PLAY_BACKWARD == Player.State.PLAY_BACKWARD:
                if self.current_frame <= 0:
                    self.current_frame = 0
                    self.play_state &= ~Player.State.PLAY_FORWARD
                    continue
                
                target = self.current_frame
                start_frame = self._find_previous_i_frame(target - 1)
                frames = []
                
                cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
                for _ in range(self.current_frame - start_frame):
                    ret, frame = cap.read()
                    
                    if not ret or not self._is_play_backward(target):
                        break
                    frames.append(frame)
                for i in reversed(frames):
                    if not self._is_play_backward(target):
                        break
                    self._display_frame(i)
                    if self.play_state & Player.State.RECORD:
                        self.record_frames.append(self.current_frame)
                    self.current_frame = target - 1
                    target = self.current_frame
                    self.ignore_slider_change = True
                    self._update_slider(self.current_frame)
                    if self.current_frame > 0:
                        time.sleep(max(float(self.durations[self.current_frame] * self.stream.time_base) - time.time() + last_time, .0))
                        last_time = time.time()
        cap.release()
        self._reencode_video(os.path.join(os.path.dirname(self.video_path), f'output{os.path.splitext(self.video_path)[1]}'))