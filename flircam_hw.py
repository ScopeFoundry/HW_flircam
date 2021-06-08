from ScopeFoundry import HardwareComponent
from .flircam_interface import FlirCamInterface
import threading
import time


IMAGE_BUFFER_SIZE = 3

default_features = {
    # lq_name: ('category', 'feature_name', dtype)
    #'exp_mode': ('AcquisitionControl', 'ExposureMode', 'enum'),
    #'exp_auto': ('AcquisitionControl', 'ExposureAuto', 'enum'),
    #'exp_time': ('AcquisitionControl', 'ExposureTime', 'float'),
    #'exp_time_abs': ('AcquisitionControl', 'ExposureTimeAbs', 'float'),
    #'frame_rate': ('AcquisitionControl', 'AcquisitionFrameRate', 'float'),
    #'AutoExposureTimeLowerLimit': ('AcquisitionControl', 'AutoExposureTimeLowerLimit', 'float'),
     'pixel_format': ('ImageFormatControl', 'PixelFormat', 'enum'),
#     ia.remote_device.node_map.PixelFormat
    }


lq_dtype_map = {
    'enum': str,
    'float': float
    }



class FlirCamHW(HardwareComponent):
    name = 'flircam'
    
    features = default_features
    
    def setup(self):
        S = self.settings
        S.New('cam_index', dtype=int, initial=0)
        S.New('auto_exposure', dtype=int, initial=2)
        S.New('acquiring', dtype=bool, initial=False)
        S.New('exposure', dtype=float, unit='s', spinbox_decimals=6, si=True)
        S.New('frame_rate', dtype=float, unit='Hz', spinbox_decimals=3)
        #S.New('pixel_format', dtype=str, choices=['UNKNOWN',])

        for lq_name, (node_name, feature_name, dtype) in self.features.items():
            print(lq_name, (node_name, feature_name, dtype))
            
            
            lq_dtype = lq_dtype_map[dtype]
            if dtype == 'enum':
                choices = ['?','?']
            else:
                choices = None
            self.settings.New(lq_name, dtype=lq_dtype, choices=choices)
        
        
    def connect(self):
        
        self.img_buffer = []
        
        S = self.settings
        self.cam = FlirCamInterface(debug=S['debug_mode'])
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
            write_func = self.start_stop_acquisition
            )     
        
        for lq_name, (cat_name, node_name, dtype) in self.features.items():
            lq = self.settings.get_lq(lq_name)
            node_type = self.cam.get_node_type(node_name)

            print(lq_name, (cat_name, node_name, dtype))
            if not self.cam.get_node_is_readable(node_name):
                print(node_name, 'Not Readable')
                continue
                
            elif dtype == 'enum':
                choices = self.cam.get_node_enum_values(node_name)
                lq.change_choice_list(choices)
                lq.update_value(self.cam.get_node_value(node_name))
            elif dtype == 'float':
                lq.update_value(self.cam.get_node_value(node_name))
                lq.change_min_max(*self.cam.get_node_value_limits(node_name))
            elif dtype == 'int':
                lq.update_value(self.cam.get_node_value(node_name))
                lq.change_min_max(*self.cam.get_node_value_limits(node_name))
            
            def read_func(nodeName=node_name):
                self.cam.get_node_value(nodeName)
            def write_func(val, nodeName=node_name):
                self.cam.set_node_value(nodeName, val)
            if not self.cam.get_node_is_writable(node_name):
                write_func = None
                lq.change_readonly(True)
            else:
                lq.change_readonly(False)
                
            lq.connect_to_hardware(read_func=read_func, write_func=write_func)
        
        
        #S.acquiring.add_listener(self.check_for_read_only)
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
            
    def start_stop_acquisition(self, start):
        if start:
            print("starting acq")
            self.cam.start_acquisition()
        else:
            print("stopping acq")
            self.cam.stop_acquisition()
        self.check_for_read_only()
    
    def check_for_read_only(self):
        print('check_for_read_only')
        time.sleep(0.001)
        for lq_name, (cat_name, node_name, dtype) in self.features.items():
            lq = self.settings.get_lq(lq_name)
            writable = self.cam.get_node_is_writable(node_name)
            print(lq_name, 'writable', writable)
            if not writable:
                lq.change_readonly(True)
            else:
                lq.change_readonly(False)

    
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