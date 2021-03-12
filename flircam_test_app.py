from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundryHW.flircam import FlirCamHW, FlirCamLiveMeasure

class FlirCamTestApp(BaseMicroscopeApp):
    
    name = 'flir_cam_test_app'
    
    def setup(self):
        hw = self.add_hardware(FlirCamHW(self))
        
        self.add_measurement(FlirCamLiveMeasure(self))
        
                
if __name__ == '__main__':
    import sys
    app = FlirCamTestApp(sys.argv)
    app.exec_()