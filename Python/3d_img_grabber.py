from __future__ import division
import numpy as np
import translator
import clr
import sys
import time

#CAMERA SETUP

source = r'C:\Users\Admin\Downloads\Scientific_Camera_Interfaces_2018_10\Scientific Camera Interfaces\SDK\DotNet Toolkit\dlls\Managed_64_lib'
sys.path.append(source)

clr.AddReference(source + r'\Thorlabs.TSI.TLCamera.dll')
clr.AddReference(source + r'\Thorlabs.TSI.TLCameraInterfaces.dll')

# Custom class from NET assembly
import Thorlabs.TSI.TLCamera
import Thorlabs.TSI.TLCameraInterfaces

cam = Thorlabs.TSI.TLCamera.TLCameraSDK.OpenTLCameraSDK()
sNum= cam.DiscoverAvailableCameras()
if sNum.Count == 0:
    print 'I\'m literally the worst'
else:
    print 'I found it cos I\'m the best'

MyCam = cam.OpenCamera(sNum[0], 0)

# MyCam Settings
MyCam.ExposureTime_us = 75000

gainRange = MyCam.GainRange
if gainRange.Maximum > 0:
    MyCam.Gain = 0

MyCam.MaximumNumberOfFramesToQueue = 1

# Data settings

length2traverse = 1000 #um
step_size       = 2 #um

FramesGimme = int(length2traverse/step_size)
saveLoc = r'C:\\Users\\Admin\\PycharmProjects\\SPIM\\data\\temp\\3d_stack'

maxPixelIntensity = 2 ** MyCam.BitDepth - 1
MyCam.OperationMode = 0
MyCam.FramesPerTrigger_zeroForUnlimited = 0
MyCam.Arm()
print 'smile'

#change motor settings
translator.m.SetJogStepSize_DeviceUnit(translator.mm2deviceUnit(step_size/1000))


#Go Time
frameCount = 0
MyCam.IssueSoftwareTrigger()

while frameCount < FramesGimme:
    #wait for frame to buffer
    while MyCam.NumberOfQueuedFrames == 0:
        time.sleep(10 ** -8)

    imageFrame = MyCam.GetPendingFrameOrNull()
    print 'frame number', imageFrame.FrameNumber, ',', frameCount, ',', FramesGimme

    imageData = imageFrame.ImageData.ImageData_monoOrBGR
    saveName = '\outableFrame%i' % frameCount
    np.save(saveLoc + saveName, list(imageData))

    #move sample
    translator.m.MoveJog(2, 10**8) # moving backwards currently

    frameCount = frameCount + 1

print 'Frames lost :(',imageFrame.FrameNumber-FramesGimme

print 'bye MyCam'
MyCam.Disarm()