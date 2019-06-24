from ScopeFoundry import Measurement
import pyqtgraph as pg
import time
import os
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path

class FlirCamLiveMeasure(Measurement):
    
    name = 'flircam_live'
    
    def setup(self):
        self.settings.New('auto_level', dtype=bool, initial=False)
        self.settings.New('crosshairs', dtype=bool, initial=False)
    
    def setup_figure(self):
        self.ui = load_qt_ui_file(sibling_path(__file__,'flircam_live_measure.ui'))
        self.hw = self.app.hardware['flircam']
        self.settings.activation.connect_to_widget(self.ui.live_checkBox)        
        self.settings.auto_level.connect_to_widget(self.ui.auto_level_checkBox)
        self.settings.crosshairs.connect_to_widget(self.ui.crosshairs_checkBox)
        
        self.hw.settings.connected.connect_to_widget(self.ui.cam_connect_checkBox)
        self.hw.settings.cam_index.connect_to_widget(self.ui.cam_index_doubleSpinBox)
        self.hw.settings.frame_rate.connect_to_widget(self.ui.framerate_doubleSpinBox)
        self.hw.settings.exposure.connect_to_widget(self.ui.exp_doubleSpinBox)
        
        
        self.imview = pg.ImageView()
        def switch_camera_view():
            self.ui.plot_groupBox.layout().addWidget(self.imview)
            self.imview.showMaximized() 
        self.ui.show_pushButton.clicked.connect(switch_camera_view)
        self.ui.plot_groupBox.layout().addWidget(self.imview)
        
        self.ui.auto_exposure_comboBox.addItem("placeholder")
        self.ui.auto_exposure_comboBox.setCurrentIndex(0)
        def apply_auto_exposure_index():
            self.hw.cam.set_auto_exposure(self.ui.auto_exposure_comboBox.currentIndex())
        self.ui.auto_exposure_comboBox.currentIndexChanged.connect(apply_auto_exposure_index)
        self.ui.save_pushButton.clicked.connect(self.save_image)

    def run(self):
        self.hw.settings['connected'] = True
        if self.ui.auto_exposure_comboBox.count() == 1:
            self.ui.auto_exposure_comboBox.addItems(self.hw.cam.get_auto_exposure_vals())
            self.ui.auto_exposure_comboBox.removeItem(0)
            self.ui.auto_exposure_comboBox.setCurrentIndex(2)

        while not self.interrupt_measurement_called:
            time.sleep(0.5)
            self.hw.settings.exposure.read_from_hardware()
        
        
    def update_display(self):
        self.display_update_period = 0.05
        im = self.hw.img_buffer.pop(0).copy()
        # print("buffer len:", len(self.hw.img_buffer))
        # self.hw.img.copy()
        self.imview.setImage(im.swapaxes(0,1),autoLevels=self.settings['auto_level'])
        
        if self.settings['crosshairs']:
            im_dims = im.shape
            if not hasattr(self,'crosshairs'):
                self.crosshairs = [pg.InfiniteLine(pos=im_dims[1]/2,angle=90, movable=False),
                                   pg.InfiniteLine(pos=im_dims[0]/2,angle=0, movable=False)]
                self.imview.getView().addItem(self.crosshairs[0])
                self.imview.getView().addItem(self.crosshairs[1])
        elif hasattr(self,'crosshairs'):
            self.imview.getView().removeItem(self.crosshairs[0])
            self.imview.getView().removeItem(self.crosshairs[1])
            del self.crosshairs
            
    def save_image(self):
        print('flircam_live_measure save_image')
        t = time.localtime(time.time())
        t_string = "{:02d}{:02d}{:02d}_{:02d}{:02d}{:02d}".format(int(str(t[0])[2:4]), t[1], t[2], t[3], t[4], t[5])
        fname = os.path.join(self.app.settings['save_dir'], "%s_%s" % (t_string, self.name))
        self.imview.export(fname + ".tif")
        self.app.settings_save_ini(fname + ".ini")
        
