import sys
from PyQt4 import QtGui, QtCore
from matplotlib import pyplot as plt
from matplotlib import animation as animation
import numpy
import time
import GUI_Design2
from GenerateThread import *
from AnalogInputThread import *
import pyqtgraph as pg
import datetime



delaytime = 3
now = datetime.datetime.now()
fil = now.strftime('%Y-%m-%d-%H:%M')

class Window(QtGui.QDialog, GUI_Design2.Ui_Dialog):

    def __init__(self, parent = None):
        super(Window, self).__init__(parent)
        self.setupUi(self)
        self.initialize()
        self.FormUpdate.clicked.connect(self.UpdateVariables)
        self.StartButton.clicked.connect(self.work)
        self.StopInput.clicked.connect(self.stopInput)
        self.StopInput.setEnabled(False)
        self.Measure.clicked.connect(self.startMeasure)
        self.wavegraph = self.waveform.addPlot(title = 'Output')
        self.gf1 = self.MeasuredB.addPlot(title='Input')
        self.G = GenerateThread()

        self.pseudoT1 = 0
        self.pseudoData1 = 0
        self.pseudoT2 = 0
        self.pseudoData2 = 0
        self.pseudo_index = 0
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateTimer)
        self.TIME_INTERVAL = 1000
        self.TIME_INTERVAL_MAX = 2000



    def initialize(self):
        self.amplitude = (float) (self.Amp.text())
        self.frequency = (float) (self.Freq.text())
        self.duration = (float) (self.Dur.text())
        self.keep_time = (float) (self.Keep.text())
        self.off_set = (int) (self.Offset.text())
        self.Device = 'Dev'+str(self.Dev.text())
        self.PORT = (float) (self.Port.text())



    def UpdateVariables(self): # Update message and move on to 'self.UpdateWaveForm()'
        self.initialize()
        self.MessageBox.append("Wave Function Generated")
        self.MessageBox.append("Amp: %s Freq: %s Dur: %s KeepTime: %s Offset: %s Device: %s Port: %s"\
        % (self.amplitude, self.frequency, self.duration, self.keep_time, self.off_set, self.Device, self.PORT))
        self.UpdateWaveForm()



    def UpdateWaveForm(self):
        self.waveform.removeItem(self.wavegraph) # Remove existed graph
        self.wavegraph = self.waveform.addPlot(title = 'Output')
        self.wavegraph.setLabel('left','Output Voltage (V)')
        self.wavegraph.setLabel('bottom','Time (s)')
        t = numpy.linspace(0, self.duration, self.duration* 20000 + 1) #Data for time
        x = self.off_set + ( (-1) * numpy.sin( 2*numpy.math.pi * self.frequency * t ) * numpy.piecewise(t, [t<self.keep_time, t>=self.keep_time], \
            [self.amplitude, lambda t: -((t-self.keep_time) * self.amplitude/(self.duration-self.keep_time))+self.amplitude]))
        #x is decreasing sinusoidal function for degaussing
        self.periodLength = len( x )
        self.time = t
        self.data = numpy.zeros( (self.periodLength, ), dtype = numpy.float64)
        self.data = x
        self.wavegraph.plot(self.time, self.data, pen='y')
        self.wavegraph.show()

    def work(self):

        self.p = ProgressBarThread(self.duration) #Connecting to live progressBar
        self.connect(self.p, QtCore.SIGNAL('itemChanged'), self.progressUpdate)
        self.connect(self.p, QtCore.SIGNAL('GenerateDone'), self.changeButton)
        self.connect(self.p, QtCore.SIGNAL('GenerateDone'), self.checkTime)
        action = self.StartButton.text()

        if action == '&Generate':

            self.StartButton.setText('&Abort') #Change label of button
            self.G.setValues(self.amplitude, self.frequency, self.duration, self.keep_time, self.off_set, self.Device, self.PORT)
            self.p.start()
            self.G.start()
            time.sleep(delaytime) #In order to match with the delay of the machine
            self.updateTimer()
            self.StartButton.clicked.connect(self.p.terminate)

        elif action == '&Abort':

            self.MessageBox.append("Aborted")
            self.StartButton.setText('&Generate')
            self.G.stop()
            self.progressBar.setValue(0)
            self.checkTime()
	    
        else:
            self.MessageBox.append('Errors: Maybe Typos in the code')



    def checkTime(self):
            self.timer.stop()
            self.pseudo_index = 0
            self.pseudoT1 = []
            self.pseudoData1 = []
            self.pseudoT2 = []
            self.pseudoData2 = []



    def startMeasure(self):
        self.MessageBox.append("Measurement began\n")
        self.Measure.setEnabled(False)
        self.StopInput.setEnabled(True)
        if self.checkflux.isChecked():
            self.fg = fluxgate(nr = 1, vrange1=10, vrange2=10, sf=100.0, taver=1, check=True)
            self.MessageBox.append("vertical axis: Magnetic Field (nT)")
        else:
            self.fg = fluxgate(nr = 1, vrange1=10, vrange2=10, sf=100.0, taver=1, check=False)
            self.MessageBox.append("vertical axis: Voltage (V)")
        self.connect(self.fg, QtCore.SIGNAL('InputUpdate'), self.state_changed)

        self.MeasuredB.removeItem(self.gf1)
        self.gf1 = self.MeasuredB.addPlot(title='Input')
        if self.checkflux.isChecked():
            self.gf1.setLabel('left','Magnetic Field (nT)')
        else:
            self.gf1.setLabel('left','Voltage (V)')

        self.gf1.setLabel('bottom','Time (s)')

        self.xcurve = self.gf1.plot(pen='r')
        self.ycurve = self.gf1.plot(pen='y')
        self.zcurve = self.gf1.plot(pen='b')

        self.gf1.enableAutoRange(x=True,y=True)

        self.fg.start() #Starting fluxgate



    def stopInput(self):
        self.fg.stop()
        self.fg.terminate()
        self.MessageBox.append("Input Task stopped\n")
        self.StopInput.setEnabled(False)
        self.Measure.setEnabled(True)



    def progressUpdate(self, value):
        """Function to show Progress"""
        self.progressBar.setValue((int)(value))



    def changeButton(self):
        self.StartButton.setText('&Generate')
        self.progressBar.setValue(0)



    def state_changed(self, (time, xar, yar, zar)):
        if self.checkX.isChecked():
            self.Xbool = True
        else:
            self.Xbool = False

        if self.checkY.isChecked():
            self.Ybool = True
        else:
            self.Ybool = False

        if self.checkZ.isChecked():
            self.Zbool = True
        else:
            self.Zbool = False
        self.restartBPlot((time, xar, yar, zar))



    def restartPlot2(self): #Live-plotting for generating a decreasing sinusoidal wave
        self.pseudo_index += 1
        self.pseudoT1 = self.time[0:self.pseudo_index*20000+1]
        self.pseudoData1 = self.data[0:self.pseudo_index*20000+1]
        self.pseudoT2 = self.time[self.pseudo_index*20000+1:]
        self.pseudoData2 = self.data[self.pseudo_index*20000+1:]
        self.waveform.removeItem(self.wavegraph)
        self.wavegraph = self.waveform.addPlot(title='Output')
        self.wavegraph.setLabel('left','Output Voltage (V)')
        self.wavegraph.setLabel('bottom','Time (s)')
        self.wavegraph.plot(self.pseudoT1, self.pseudoData1, pen='g')
        self.wavegraph.plot(self.pseudoT2, self.pseudoData2, pen='y')



    def updateTimer(self):
        self.restartPlot2()
        self.timer.start(self.TIME_INTERVAL)




    def restartBPlot(self, (time, xar, yar, zar)): #Updating inputdata for every one second
        self.t = time
        self.xar = xar
        self.yar = yar
        self.zar = zar


        if self.Xbool == True:
            self.xcurve.setData(x= self.t, y=self.xar) #If t and xar is changed, automatically re-plot the graph
        else:
            self.xcurve.setData(x=[], y = [])
        if self.Ybool == True:
            self.ycurve.setData(x= self.t, y=self.yar)
        else:
            self.ycurve.setData(x=[], y = [])
        if self.Zbool == True:
            self.zcurve.setData(x= self.t, y=self.zar)
        else:
            self.zcurve.setData(x=[], y = [])





class ProgressBarThread(QtCore.QThread):


    def __init__(self, duration, parent = None):
        super(ProgressBarThread, self).__init__(parent)
        self.duration = duration
        self.running = True



    def run(self):
        value = 0
        value_max = 100
        time.sleep(delaytime)
        while value < value_max:
            value = value + (10/self.duration)
            self.emit(QtCore.SIGNAL('itemChanged'), value)
            time.sleep(0.1)
        time.sleep(2)
        self.emit(QtCore.SIGNAL('GenerateDone'))




def start_app(): #Starting an application
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    app.exec_()


if __name__ == '__main__':
    start_app()


