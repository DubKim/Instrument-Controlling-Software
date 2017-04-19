#This routine creates the actual waveform as well as providing a structure for plotting it
import numpy
from matplotlib import pyplot as plt
from WaveformThread import *

class Degausser():
    def __init__(self, device, chnnr):
        self.device = device
        self.chnnr = chnnr

    def createNpWaveform(self, amp, freq, offset, duration, keeptime, sampleRate):
        '''create waveform from given parameters'''
        self.sampleRate = sampleRate
        t = numpy.linspace(0, duration, duration*sampleRate + 1)
        x = offset + ( (-1) * numpy.sin( 2*numpy.math.pi * freq * t ) * numpy.piecewise(t, [t<keeptime, t>=keeptime], \
                                                                                        [amp, lambda t: -((t-keeptime) * amp/(duration-keeptime))+amp]))
        self.periodLength = len( x )
        self.time = t
        self.data = numpy.zeros( (self.periodLength, ), dtype = numpy.float64)  #I'm assuming I don't need to define float64
        self.data = x

        #Here I define the global versions of x and t for displaying on the GUI

    def plotWaveform(self):
        plt.plot(self.time, self.data)
        plt.show()

    def playWaveform(self):
        self.wavethread = WaveformThread(self.device, self.chnnr, self.data, self.sampleRate, self.time)
        self.wavethread.run()
        self.wavethread.__del__()
        self.wavethread = None

    def abortWaveform(self):
        if self.wavethread:
            self.wavethread.stop()


