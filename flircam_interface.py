import ctypes
from ctypes import byref, c_void_p, c_int, c_size_t, c_uint,c_uint16,POINTER,c_uint8, c_double
from .flircam_consts import FlirCamErrors
import platform
import logging
from threading import Lock
import time
from numpy.ctypeslib import as_array
import numpy as np

logger = logging.getLogger(__name__)
MAX_BUFF_LEN = 256

def _err(retval):
    if retval == 0:
        return retval
    else:
        err_name = FlirCamErrors.get(retval)
        raise IOError( "Flircam Error {}: {}".format(retval, err_name))
        raise IOError( "Flircam Error {}".format(retval))

class FlirCamInterface(object):
    
    def __init__(self, debug=False):
        self.debug = debug
        
        if platform.architecture()[0] == '64bit':
            libpath = r"C:\Program Files\Point Grey Research\Spinnaker\bin64\vs2015\SpinnakerC_v140.dll"
        else:
            libpath = r"C:\Program Files\Point Grey Research\Spinnaker\bin\vs2015\SpinnakerC_v140.dll"
            
        self.lib = ctypes.cdll.LoadLibrary(libpath)
        self.lock = Lock()
        
        if self.debug: print("Flircam initializing")
        
        with self.lock:
            self.hSystem = c_void_p()
            _err(self.lib.spinSystemGetInstance(byref(self.hSystem)))
            if self.debug: print("hSystem " + str(self.hSystem))
            
            self.hCameraList = c_void_p()
            _err(self.lib.spinCameraListCreateEmpty(byref(self.hCameraList)))
            _err(self.lib.spinSystemGetCameras(self.hSystem, self.hCameraList))
            if self.debug: print("hCameraList " + str(self.hCameraList))
            
            self.numCameras = c_size_t(0)
            _err(self.lib.spinCameraListGetSize(self.hCameraList, byref(self.numCameras)))
            
        if self.numCameras == 0:
            self.release_system()
            if self.debug: print("No cameras connected!")
        elif self.numCameras.value > 1:
            if self.debug: 
                print(str(self.numCameras) + " cameras detected.")
                print("Connecting to first camera")
        
        self.hCamera = c_void_p()
        _err(self.lib.spinCameraListGet(self.hCameraList, 0, byref(self.hCamera)))
        if self.debug: print("hCamera " + str(self.hCamera))
        
        hNodeMapTLDevice = c_void_p()
        _err(self.lib.spinCameraGetTLDeviceNodeMap(self.hCamera, byref(hNodeMapTLDevice)))
        if self.debug: print("hNodeMapTLDevice " + str(hNodeMapTLDevice))
        
        if self.debug: print("Initializing camera")
        _err(self.lib.spinCameraInit(self.hCamera))
        
        self.hNodeMap = c_void_p()
        _err(self.lib.spinCameraGetNodeMap(self.hCamera, byref(self.hNodeMap)))
        if self.debug: print("hNodeMap " + str(self.hNodeMap))
        
        hAcquisitionMode = c_void_p()
        _err(self.lib.spinNodeMapGetNode(self.hNodeMap, b"AcquisitionMode", byref(hAcquisitionMode)))
        if self.debug: print("hAcquisitionMode " + str(hAcquisitionMode))
        
        if self.debug: print("Setting acquisition mode to continuous.")
        _err(self.lib.spinEnumerationSetIntValue(hAcquisitionMode, self.get_enum_int_by_name(hAcquisitionMode, b'Continuous')))
        
        self.start_acquisition()
        
    def start_acquisition(self):
        if self.debug: print("Starting acquisition")
        _err(self.lib.spinCameraBeginAcquisition(self.hCamera))
        
    def stop_acquisition(self):
        if self.debug: print("Stopping acquisition")
        _err(self.lib.spinCameraEndAcquisition(self.hCamera))
        
    def get_image(self, save_jpg=False):
        hResultImage = c_void_p()
        isIncomplete = ctypes.c_bool(True)
        if self.debug: print("Grabbing image")
        while isIncomplete:
            _err(self.lib.spinCameraGetNextImage(self.hCamera, byref(hResultImage)))
            _err(self.lib.spinImageIsIncomplete(hResultImage, byref(isIncomplete)))
            if isIncomplete: # cleanup incomplete images to avoid memory leaks
                _err(self.lib.spinImageRelease(hResultImage))
        
        if self.debug: print("hResultImage " + str(hResultImage))

        width = ctypes.c_uint(0)
        height = ctypes.c_uint(0)
        
        _err(self.lib.spinImageGetWidth(hResultImage,byref(width) ))
        _err(self.lib.spinImageGetHeight(hResultImage,byref(height) ))
        
        if self.debug: print("w x h: %d %d" % (width.value,height.value))
        
        hConvertedImage = c_void_p()
        _err(self.lib.spinImageCreateEmpty(byref(hConvertedImage)))
        _err(self.lib.spinImageConvert(hResultImage, 0, hConvertedImage))
        
        if self.debug: print("hConvertedImage " + str(hConvertedImage))
        
        self.lib.spinImageGetData.argtypes = (c_void_p,POINTER(POINTER(c_uint16)))
        self.lib.spinImageGetData.restype = c_uint8
        ppData = POINTER(c_uint16)()
        pSize = c_uint(0)
        _err(self.lib.spinImageGetData(hResultImage, ppData))
        _err(self.lib.spinImageGetBufferSize(hResultImage, byref(pSize)))
        
        retval = as_array(ppData,(1200,1920))
        
        if save_jpg:
            t0 = time.time()
            _err(self.lib.spinImageSave(hResultImage, b"flircam_test_%i.jpg" % t0, -1))

        _err(self.lib.spinImageDestroy(hConvertedImage))
        _err(self.lib.spinImageRelease(hResultImage))
        
        return retval
        
        
    def release_camera(self):
        if hasattr(self,'hCamera'):
            _err(self.lib.spinCameraRelease(self.hCamera))
        
    def release_system(self):
        if hasattr(self,'hCameraList'):
            _err(self.lib.spinCameraListClear(self.hCameraList))
            _err(self.lib.spinCameraListDestroy(self.hCameraList))
        if hasattr(self,'hSystem'):
            _err(self.lib.spinSystemReleaseInstance(self.hSystem))
        
    def get_enum_int_by_name(self, hEnumNode, name):
        hEnumEntry = c_void_p()
        enumInt = c_int()
        _err(self.lib.spinEnumerationGetEntryByName(hEnumNode, name, byref(hEnumEntry)))
        _err(self.lib.spinEnumerationEntryGetIntValue(hEnumEntry, byref(enumInt)))
        return enumInt.value
    
    def get_enum_name_by_int(self, hEnumNode, index):
        hEnumEntry = c_void_p()
        enumInd = c_uint(index)
        _err(self.lib.spinEnumerationGetEntryByIndex(hEnumNode, enumInd, byref(hEnumEntry)))
        
        enumSym = ctypes.create_string_buffer(MAX_BUFF_LEN)
        lenEnumSym = c_size_t(MAX_BUFF_LEN)
        _err(self.lib.spinEnumerationEntryGetSymbolic(hEnumEntry,byref(enumSym),byref(lenEnumSym)))

        return str(enumSym.value,'utf8')
            
    def print_device_info(self):
        print("\n*** FLIRCAM DEVICE INFORMATION ***\n\n")
        hNodeMapTLDevice = c_void_p()
        _err(self.lib.spinCameraGetTLDeviceNodeMap(self.hCamera, byref(hNodeMapTLDevice)))
        if self.debug: print("hNodeMapTLDevice " + str(hNodeMapTLDevice))
        
        # Retrieve device information category node
        hDeviceInformation = c_void_p()
        _err(self.lib.spinNodeMapGetNode(hNodeMapTLDevice, b"DeviceInformation", byref(hDeviceInformation)))
        if self.debug: print('hDeviceInformation ' + str(hDeviceInformation))
        
        # Retrieve number of nodes within device information node
        numFeatures = c_uint(0)
        _err(self.lib.spinCategoryGetNumFeatures(hDeviceInformation, byref(numFeatures)))
        
        # Iterate through nodes and print information
        for i in range(numFeatures.value):
            hFeatureNode = c_void_p()
            ii = c_size_t(i)
            _err(self.lib.spinCategoryGetFeatureByIndex(hDeviceInformation, ii, byref(hFeatureNode)))

            featureType = c_int(-1);

            # get feature node name
            featureName = ctypes.create_string_buffer(MAX_BUFF_LEN)
            lenFeatureName = c_size_t(MAX_BUFF_LEN)
            _err(self.lib.spinNodeGetName(hFeatureNode, featureName, byref(lenFeatureName)))
            _err(self.lib.spinNodeGetType(hFeatureNode, byref(featureType)))
        
            featureValue = ctypes.create_string_buffer(MAX_BUFF_LEN)
            lenFeatureValue = c_size_t(MAX_BUFF_LEN)

            _err(self.lib.spinNodeToString(hFeatureNode, featureValue, byref(lenFeatureValue)))

            print("%s: %s" % (str(featureName.value,'utf8'), str(featureValue.value,'utf8')))
    
    def get_exposure_time(self):
        hExposureTime = self.get_node(b"ExposureTime")
    
        exp_time = c_double()
        _err(self.lib.spinFloatGetValue(hExposureTime,byref(exp_time)))
        if self.debug: print("exp_time " + str(exp_time))

        return exp_time.value*1e-6
    
    def set_exposure_time(self,t):
        hExposureTime = self.get_node(b"ExposureTime")
        (minval, maxval) = self.get_exposure_lims()
        exp_time = c_double(max(min(t,maxval),minval))
        _err(self.lib.spinFloatSetValue(hExposureTime,exp_time*1e6))
    
    def get_node(self,nodeName):
        nodeHandle = c_void_p()
        _err(self.lib.spinNodeMapGetNode(self.hNodeMap,nodeName,byref(nodeHandle)))
        if self.debug: print("%s: %s" % (str(nodeName,'utf8'),str(nodeHandle)))
        return nodeHandle
             
    def get_auto_exposure(self):
        hExposureAuto = self.get_node(b"ExposureAuto")
        
        phExposureAuto = c_void_p()
        ExposureAuto = ctypes.create_string_buffer(MAX_BUFF_LEN)
        lenExposureAuto = c_size_t(MAX_BUFF_LEN)
        indValExposureAuto = c_uint()
        _err(self.lib.spinEnumerationGetCurrentEntry(hExposureAuto,byref(phExposureAuto)))
        if self.debug: print("phExposureAuto " + str(phExposureAuto))
        _err(self.lib.spinEnumerationEntryGetSymbolic(phExposureAuto,byref(ExposureAuto),byref(lenExposureAuto)))
        if self.debug: print("ExposureAuto " + str(ExposureAuto.value,'utf8'))
        _err(self.lib.spinEnumerationEntryGetIntValue(phExposureAuto,byref(indValExposureAuto)))
        if self.debug: print("indValExposureAuto %d" % indValExposureAuto.value)
                
        return indValExposureAuto.value
    
    def set_auto_exposure(self,ind):
        hExposureAuto = self.get_node(b"ExposureAuto")
        setIndex = self.get_auto_exposure()
        numVals = int(np.size(self.get_auto_exposure_vals()))
        if ind == setIndex:
            return
        elif ind < numVals:
            _err(self.lib.spinEnumerationSetIntValue(hExposureAuto,ind))
        else: 
            print("Error! Cannot set that auto exposure value")
    
    def get_node_enum_values(self,nodeName):
        nodeHandle = self.get_node(nodeName)
        numVals = c_uint()
        _err(self.lib.spinEnumerationGetNumEntries(nodeHandle,byref(numVals)))
        
        enumList = list()
        for i in range(numVals.value):
            this_val = self.get_enum_name_by_int(nodeHandle, i)
            enumList.append(this_val)
            if self.debug: print("%d %s" % (i, this_val))
        return enumList
        
    def get_auto_exposure_vals(self):
        return self.get_node_enum_values(b"ExposureAuto")
        
    def get_frame_rate(self):
        hAcquisitionFrameRate = self.get_node(b"AcquisitionFrameRate")
        frameRate = c_double()
        _err(self.lib.spinFloatGetValue(hAcquisitionFrameRate,byref(frameRate)))
        return frameRate.value
    
    def set_frame_rate(self,val):
        pass
        
    def get_exposure_lims(self):
        hExposureTime = self.get_node(b"ExposureTime")
    
        exp_time_min = c_double()
        exp_time_max = c_double()
        
        _err(self.lib.spinFloatGetMin(hExposureTime,byref(exp_time_min)))
        _err(self.lib.spinFloatGetMax(hExposureTime,byref(exp_time_max)))
        retval = (exp_time_min.value*1e-6,exp_time_max.value*1e-6)
        if self.debug: print("exp_time lims %f %f" % retval)

        return retval
        
if __name__ == '__main__':
    #print(sys.path)
    try: 
        cam = FlirCamInterface(debug=True)
        cam.start_acquisition()
        cam.print_device_info()
        test_data = cam.get_image(save_jpg=False)
        print(cam.get_exposure_time())
        print(cam.get_auto_exposure())
        print(cam.get_auto_exposure_vals())
        print(cam.get_frame_rate())
        print(cam.get_exposure_lims())
    except Exception as ex:
        print('error: ' + str(ex))
    print(test_data)
    cam.stop_acquisition()
    cam.release_camera()
    cam.release_system()
    