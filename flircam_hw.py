from ScopeFoundry import HardwareComponent
from .flircam_interface import FlirCamInterface
import threading
import time


IMAGE_BUFFER_SIZE = 16

class FlirCamHW(HardwareComponent):
    name = 'flircam'
    
    def setup(self):
        S = self.settings
        S.New('cam_index', dtype=int, initial=0)
        S.New('auto_exposure', dtype=int, initial=2)
        S.New('acquiring', dtype=bool, initial=False)
        S.New('exposure', dtype=float, unit='s', spinbox_decimals=3)
        S.New('frame_rate', dtype=float, unit='Hz', spinbox_decimals=3)
        
    def connect(self):
        
        self.img_buffer = []
        
        S = self.settings
        self.cam = FlirCamInterface(debug=False)
        S.debug_mode.add_listener(self.set_debug_mode)
        S.auto_exposure.connect_to_hardware(
            read_func = self.cam.get_auto_exposure,
            write_func = self.cam.set_auto_exposure
            )
        S.auto_exposure.read_from_hardware()
        S.exposure.connect_to_hardware(
            read_func = self.cam.get_exposure_time,
            write_func = self.cam.set_exposure_time
            )
        S.exposure.read_from_hardware()
        S.frame_rate.connect_to_hardware(
            read_func = self.cam.get_frame_rate,
            write_func = self.cam.set_frame_rate
            )
        
        S.acquiring.connect_to_hardware(
            write_func = self.cam.set_acquisition
            )
        S.acquiring.update_value(True)
        self.update_thread_interrupted = False
        self.update_thread = threading.Thread(target=self.update_thread_run)
        self.update_thread.start()
        
    def disconnect(self):
        self.settings.acquiring.update_value(False)
        self.settings.disconnect_all_from_hardware()
       
        if hasattr(self,'update_thread'):
            self.update_thread_interrupted = True
            self.update_thread.join(timeout=1.0)
            del self.update_thread
        
        if hasattr(self,'cam'):
            self.cam.stop_acquisition()
            self.cam.release_camera()
            self.cam.release_system()
            del self.cam
    
    def update_thread_run(self):
        while not self.update_thread_interrupted:
            if self.settings['acquiring']:
                self.img = self.cam.get_image()
                self.img_buffer.append(self.img)
                if len(self.img_buffer) > IMAGE_BUFFER_SIZE:
                    self.img_buffer = self.img_buffer[-IMAGE_BUFFER_SIZE:]
                self.settings.frame_rate.read_from_hardware()
            #time.sleep(1/self.settings['frame_rate'])
        
    def set_debug_mode(self):
        self.cam.debug = self.settings['debug_mode']