import ctypes
from ctypes import byref, c_void_p, c_int, c_size_t, c_uint,c_uint16,POINTER,c_uint8, c_double,\
    c_ulonglong
from .flircam_consts import FlirCamErrors, FlirCamImageStatus
import platform
import logging
from threading import Lock
import time
import numpy as np


logger = logging.getLogger(__name__)
MAX_BUFF_LEN = 256

def _err(retval):
    if retval == 0:
        return retval
    else:
        err_name = list(FlirCamErrors.keys())[list(FlirCamErrors.values()).index(retval)]
        raise IOError( "Flircam Error {}: {}".format(retval, err_name))
        raise IOError( "Flircam Error {}".format(retval))

class FlirCamInterface(object):
    def __init__(self, debug=False):
        self.debug = debug
        self.acquiring = False
        
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
        
    def set_acquisition(self, val):
        if self.debug: print('setting acquisition to %i' % val)
        if val:
            self.start_acquisition()
        else:
            self.stop_acquisition()
        
    def start_acquisition(self):
        if self.debug: print("Starting acquisition")
        if not self.acquiring:
            _err(self.lib.spinCameraBeginAcquisition(self.hCamera))
        
    def stop_acquisition(self):
        if self.debug: print("Stopping acquisition")
        if self.acquiring: 
            _err(self.lib.spinCameraEndAcquisition(self.hCamera))
        
    def get_image(self, save_jpg=False):
        hResultImage = c_void_p()
        isIncomplete = ctypes.c_bool(True)
        imageStatus = c_uint(-1)
        if self.debug: print("Grabbing image")
        with self.lock:
            _err(self.lib.spinCameraGetNextImage(self.hCamera, byref(hResultImage)))
            _err(self.lib.spinImageIsIncomplete(hResultImage, byref(isIncomplete)))
            _err(self.lib.spinImageGetStatus(hResultImage, byref(imageStatus)))
            
            while isIncomplete and imageStatus != 0:
                if self.debug: print('incomplete',imageStatus)
                if imageStatus != 0:
                    print(FlirCamImageStatus[imageStatus])
                _err(self.lib.spinImageRelease(hResultImage))
                _err(self.lib.spinCameraGetNextImage(self.hCamera, byref(hResultImage)))
                _err(self.lib.spinImageIsIncomplete(hResultImage, byref(isIncomplete)))
                _err(self.lib.spinImageGetStatus(hResultImage, byref(imageStatus)))       
            
            if self.debug: print("hResultImage " + str(hResultImage))
    
            width = ctypes.c_uint(0)
            height = ctypes.c_uint(0)
            
            _err(self.lib.spinImageGetWidth(hResultImage,byref(width) ))
            _err(self.lib.spinImageGetHeight(hResultImage,byref(height) ))
            
            if self.debug: print("w x h: %d %d" % (width.value,height.value))
            
            # hConvertedImage = c_void_p()
            # _err(self.lib.spinImageCreateEmpty(byref(hConvertedImage)))
            # _err(self.lib.spinImageConvert(hResultImage, 0, hConvertedImage))
            
            # if self.debug: print("hConvertedImage " + str(hConvertedImage))
            
            #self.lib.spinImageGetData.argtypes = (c_void_p,POINTER(POINTER(c_uint16)))
            #self.lib.spinImageGetData.restype = c_uint8
            #ppData = POINTER(c_uint16)()
            #_err(self.lib.spinImageGetData(hResultImage, ppData))
            #img = np.array(np.ctypeslib.as_array(ppData,(1200,1920)))
            #del ppData
            #img = np.ones((1200,1920),dtype=np.uint16)
#             _err(self.lib.spinImageGetData(hResultImage, byref(img.ctypes.data_as(POINTER(c_uint16)))))
#             
            pBitsPerPixel=c_uint(0)
            _err(self.lib.spinImageGetBitsPerPixel(hResultImage, byref(pBitsPerPixel)))
            #print(pBitsPerPixel.value)
            
            
            pSize = c_uint(0)
            _err(self.lib.spinImageGetBufferSize(hResultImage, byref(pSize)))
            data = np.zeros(1, dtype=c_void_p)
            _err(self.lib.spinImageGetData(hResultImage, data.ctypes))
            if self.debug: print(data)
            
            if pBitsPerPixel.value == 8:
                #print('8bits')
                img = np.frombuffer((c_uint8*pSize.value).from_address(int(data[0])), dtype=c_uint8)
            elif pBitsPerPixel.value == 16:
                #print('16bits')
                img = np.frombuffer((c_uint8*pSize.value).from_address(int(data[0])), dtype=c_uint16)
            
            if self.debug:
                print(img.shape)
                print(img.shape, img.reshape(1200,1920).shape)           
                        
            if save_jpg:
                t0 = time.time()
                _err(self.lib.spinImageSave(hResultImage, b"flircam_test_%i.jpg" % t0, -1))
    
            # _err(self.lib.spinImageDestroy(hConvertedImage))
            _err(self.lib.spinImageRelease(hResultImage))
            return img.reshape((1200,1920))
        
#
# // Assuming image is 640 x 480 resolution. The current pixel format as well as PixelColorFilter indicate the Bayer Tile Mapping for the camera. For example, BayerRG8 is RGGB. 
# 
# err = spinCameraGetNextImage(hCam, &hResultImage);
# size_t imageSize;
# spinImageGetBufferSize(hResultImage, &imageSize);
# 
# void **data;
# data = (void**)malloc(imageSize * sizeof(void*));
# 
# spinImageGetData(hResultImage, data);



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
        hExposureTime = self.get_node("ExposureTime")
    
        exp_time = c_double()
        _err(self.lib.spinFloatGetValue(hExposureTime,byref(exp_time)))
        if self.debug: print("exp_time " + str(exp_time))

        return exp_time.value*1e-6
    
    def set_exposure_time(self,t):
        hExposureTime = self.get_node("ExposureTime")
        (minval, maxval) = self.get_exposure_lims()
        exp_time = c_double(max(min(t,maxval),minval))
        _err(self.lib.spinFloatSetValue(hExposureTime,exp_time*1e6))
    
    def get_node(self,nodeName):
        nodeHandle = c_void_p()
        if isinstance(nodeName, str):
            nodeName = nodeName.encode('utf-8')
        _err(self.lib.spinNodeMapGetNode(self.hNodeMap,nodeName,byref(nodeHandle)))
        if self.debug: print("%s: %s" % (nodeName,str(nodeHandle)))
        return nodeHandle
             
    def get_auto_exposure(self):
#         hExposureAuto = self.get_node("ExposureAuto")
#         
#         phExposureAuto = c_void_p()
#         ExposureAuto = ctypes.create_string_buffer(MAX_BUFF_LEN)
#         lenExposureAuto = c_size_t(MAX_BUFF_LEN)
#         indValExposureAuto = c_uint()
#         _err(self.lib.spinEnumerationGetCurrentEntry(hExposureAuto,byref(phExposureAuto)))
#         if self.debug: print("phExposureAuto " + str(phExposureAuto))
#         _err(self.lib.spinEnumerationEntryGetSymbolic(phExposureAuto,byref(ExposureAuto),byref(lenExposureAuto)))
#         if self.debug: print("ExposureAuto " + str(ExposureAuto.value,'utf8'))
#         _err(self.lib.spinEnumerationEntryGetIntValue(phExposureAuto,byref(indValExposureAuto)))
#         if self.debug: print("indValExposureAuto %d" % indValExposureAuto.value)
        return self.get_node_enum_index('ExposureAuto')
    
    def set_auto_exposure(self,ind):
        hExposureAuto = self.get_node("ExposureAuto")
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
    
    def get_pixel_format_vals(self):
        return self.get_node_enum_values(b"PixelFormat")
    
    def get_node_enum_index(self, nodeName):
        hEnum = self.get_node(nodeName)
        pEnum = c_void_p()
        enumSymbolic = ctypes.create_string_buffer(MAX_BUFF_LEN)
        lenSymbolic = c_size_t(MAX_BUFF_LEN)
        enumIndex = c_uint()
        
        _err(self.lib.spinEnumerationGetCurrentEntry(hEnum,byref(pEnum)))
        if self.debug: print("ph%s %s" % (nodeName, str(pEnum)))
        _err(self.lib.spinEnumerationEntryGetSymbolic(pEnum,byref(enumSymbolic),byref(lenSymbolic)))
        if self.debug: print("%s %s" % (nodeName, str(enumSymbolic.value,'utf8')))
        _err(self.lib.spinEnumerationEntryGetIntValue(pEnum,byref(enumIndex)))
        if self.debug: print("indVal%s %d" % (nodeName, enumIndex.value))
        return enumIndex.value
    
    def get_pixel_format(self):
#         hPixelFormat = self.get_node(b"PixelFormat")
#         
#         phPixelFormat = c_void_p()
#         PixelFormat = ctypes.create_string_buffer(MAX_BUFF_LEN)
#         lenPixelFormat = c_size_t(MAX_BUFF_LEN)
#         indValPixelFormat = c_uint()
#         _err(self.lib.spinEnumerationGetCurrentEntry(hPixelFormat,byref(phPixelFormat)))
#         if self.debug: print("phPixelFormat " + str(phPixelFormat))
#         _err(self.lib.spinEnumerationEntryGetSymbolic(phPixelFormat,byref(PixelFormat),byref(lenPixelFormat)))
#         if self.debug: print("PixelFormat " + str(PixelFormat.value,'utf8'))
#         _err(self.lib.spinEnumerationEntryGetIntValue(phPixelFormat,byref(indValPixelFormat)))
#         if self.debug: print("indValPixelFormat %s" % str(indValPixelFormat.value))
        return self.get_node_enum_index('PixelFormat')
        
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
    except Exception as ex:
        print('error: ' + str(ex))

    cam.print_device_info()
    print(len(cam.get_pixel_format_vals()))
    print(cam.get_pixel_format())
    print(len(cam.get_auto_exposure_vals()))
    print(cam.get_auto_exposure())
            
    cam.get_node_enum_index('ExposureAuto')
    cam.get_node_enum_index('PixelFormat')
    cam.stop_acquisition()
    cam.release_camera()
    cam.release_system()
    