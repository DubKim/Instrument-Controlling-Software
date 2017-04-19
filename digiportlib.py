import ctypes
import numpy
import time
import nidaqmx


#The voltage divider used was previously defined in a dictionary but I have now set it to 2
#These are the setups for national instruments to create an output task. It would be better not to change this one.

class VoltageDivider():
    def __init__(self, dev):
        self.dev = dev
        self.output_str = dev+"/port0/line5:7"
        self.dotask = nidaqmx.DigitalOutputTask()
        self.dotask.create_channel(self.output_str)

    def resetall(self):
        ddat = numpy.ones(3, dtype = numpy.uint8)
        ddat[2] = 0
        self.dotask.write(ddat, auto_start = True, layout = "group_by_channel")
        time.sleep(0.1)
        ddat[2] = 1
        self.dotask.write(ddat, auto_start = True, layout = "group_by_channel")

    def setnr(self, nr):
        self.resetall()
        ddat = numpy.ones(3, dtype = numpy.uint8)
        ddat[nr] = 0
        self.dotask.write(ddat, auto_start = True, layout = "group_by_channel")
        time.sleep(0.1)
        ddat[nr] = 1
        self.dotask.write(ddat, auto_start = True, layout = "group_by_channel")


class DigitalInput():
    def __init__(self, dev):
        self.dev = dev
        # Digital Input channels for readout of degaussing coil relays
        self.input_str = dev+"/port1/line0:7,"+dev+"/port2/line6:7"
        self.ditask = nidaqmx.DigitalInputTask()
        self.ditask.create_channel(self.input_str)

    def read(self):
        return self.ditask.read(1)[0][0]

class DigitalOutput():
    def __init__(self, dev, channels):
        self.dev = dev
        self.nrchans = int(channels.split(":")[1]) - int(channels.split(":")[0]) + 1
        self.output_str = dev+"/port0/line" + str(channels)
        self.dotask = nidaqmx.DigitalOutputTask()
        self.dotask.create_channel(self.output_str, name = "line"
                +str(channels))

    def switch(self, nr):
        ddat = numpy.ones(self.nrchans, dtype = numpy.uint8)
        ddat[nr] = 0
        self.dotask.write(ddat, auto_start = True, layout = "group_by_channel")
        time.sleep(0.1)
        ddat[nr] = 1
        self.dotask.write(ddat, auto_start = True, layout = "group_by_channel")
        time.sleep(0.1)

class SwitchCoil():
    def __init__(self, dev):
        self.di = DigitalInput(dev)
        self.do = DigitalOutput(dev, "0:4")
        self.nrchans = 5

    def alloff(self):
        curstate = self.di.read()
        s1 = curstate[0::2]
        s2 = curstate[1::2]
        con = (s1==s2)
        if 0 in s1:
            curon = numpy.where(s1==0)[0]
            #print curon
            for a in curon:
                if con[a]:
                    self.do.switch(a)
                else:
                    raise Exception("Error: The two relays for coil {} are not in same state".format(a))


    def deactivate(self, nr):
        self.do.switch(nr)
        time.sleep(0.1)

    def activate(self, nr):
        if nr > self.nrchans-1:
            pass
        else:
            curstate = self.di.read()
            s1 = curstate[0::2]
            s2 = curstate[1::2]
            con = (s1==s2)
            if 0 in s1:
                curon = numpy.where(s1==0)[0]
                #print curon
                for a in curon:
                    if con[a]:
                        self.do.switch(a)
                    else:
                        raise Exception("Error: The two relays for coil {} are not in same state".format(a))
            if s1[nr] == 0:
                pass
            if s1[nr] == 1:
                self.do.switch(nr)
