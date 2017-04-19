from PyQt4 import QtCore
from digiportlib import *
from Degausser import *

class GenerateThread(QtCore.QThread): #Genearting an output task as a multi-thread

    def __init__(self, parent = None):
        super(GenerateThread, self).__init__(parent)


    def setValues(self, amp, freq, dur, keeptime, offset, device, RelayPort):
        self.amp = amp
        self.freq = freq
        self.dur = dur
        self.keeptime = keeptime
        self.offset = offset
        self.device = (str) (device)
        self.RelayPort = RelayPort
        self._voltagedividerUsed = 2
        self.degauss = Degausser(self.device, 1)

    def run(self):

        #Below are just the setups before generating an output task.

        swc = SwitchCoil(self.device)
        swc.alloff()
        vd = VoltageDivider(self.device)
        vd.resetall()
        time.sleep(1)
        self.degauss.createNpWaveform(self.amp, self.freq, self.offset, self.dur, self.keeptime, 20000)
        vd.setnr(self._voltagedividerUsed)
        swc.activate(self.RelayPort)
        time.sleep(1)
        self.degauss.playWaveform()
        swc.deactivate(self.RelayPort)
        time.sleep(0.5)
        vd.resetall()

    def stop(self):
        self.degauss.abortWaveform()