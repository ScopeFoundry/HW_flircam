from ScopeFoundryHW.flircam.flircam_interface import FlirCamInterface

#try: 
cam = FlirCamInterface(debug=False)
#except Exception as ex:
#    print('error: ' + str(ex))
    
cam.print_device_info()
#print(len(cam.get_pixel_format_vals()))
print(cam.get_pixel_format())
#print(len(cam.get_auto_exposure_vals()))
print(cam.get_auto_exposure())
for x in ['PixelFormat', 'ExposureAuto', 'AcquisitionFrameRate']:
    print("Node {}".format(x))
    print('\t Type \t {}'.format(cam.get_node_type(x)))
    print('\t Readable \t {}'.format(cam.get_node_is_readable(x)))
    print('\t Writable \t {}'.format(cam.get_node_is_writable(x)))
    print('\t Value \t {}'.format(cam.get_node_value(x)))
    
cam.set_node_value('PixelFormat', 'RGB8')

print("new pix format", cam.get_node_value('PixelFormat'))
    
cam.start_acquisition()

cam.get_node_enum_index('ExposureAuto')
cam.get_node_enum_index('PixelFormat')
cam.stop_acquisition()
cam.release_camera()
cam.release_system()
