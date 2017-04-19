import nidaqmx
import numpy as np
import datetime
from PyQt4 import QtCore
import time
import sys

"""
This code is for analog input. There is a variable called 'nr', and it is a number of magnetic field sensor you are using.
Since a magnetic field sensor consists of three ports (x, y, z), the number of ports equals to 3 X nr.
"""

now = datetime.datetime.now()
fil = now.strftime('%Y_%m_%d_%Hh_%Mm') # File will be saved as (example) "2016_09_03_05h_12m.txt" Data file

class fluxgate(QtCore.QThread): # Analog Input Task
    def __init__(self, nr = 1, vrange1=10, vrange2=10, sf=100.0, taver=1, check=True, parent = None):
        super(fluxgate, self).__init__(parent)
        self.volt_range1 = vrange1 #minimum voltage
        self.volt_range2 = vrange2 #maximum voltage
        self.average_time = taver
        self.sf = sf #sample frequency / data per second
        self.nr = nr #number of sensor
        self.task = nidaqmx.AnalogInputTask() #Creating a task
        self.t = []
        self.xar = []
        self.yar = []
        self.zar = []
        self.check = check
        self.samples = int(self.sf*self.average_time) #Number of full samples

    def run(self):
        if self.nr == 1: #If there is only one sensor
            self.task.create_voltage_channel('Dev1/ai14,Dev1/ai7,Dev1/ai11', terminal = 'rse', min_val=-self.volt_range1, max_val=self.volt_range1)
        elif self.nr == 2: # If there are two sensors
            self.task.create_voltage_channel('Dev1/ai14,Dev1/ai7,Dev1/ai11,Dev1/ai0,Dev1/ai1,Dev1/ai2', terminal = 'rse', min_val=-self.volt_range2, max_val=self.volt_range2)
        else:
            raise ValueError("Wrong number of sensors, 1 or 2 sensors are available")

        self.task.configure_timing_sample_clock(rate = self.sf) # Defining how many samples you are going to get
        self.task.start() #Starting the task
        self.measure_to_file(fil)

    def measure_to_file(self, filename):
        fil = 'C:/Users/fieldcontrol/Degausser_final/Data/'+filename+'.txt' #File Directory
        initialtime = (int) (time.time()) #Variable for calculating time in seconds

        with open(fil, "w") as f:
            i = 0
            self.time_index = [(t/(float)(self.samples)) for t in range(self.samples)]
            self.time_memory = self.time_index

            while i < 36000:
                i = i+1
                x_val, y_val, z_val = self.readvalues()
                #print("{3} {0:.5f} {1:.5f} {2:.5f} {4} {5} {6}".format(read[0], read[1], read[2], now, std[0], std[1], std[2]))
                #print("{0} {1} {2}".format(now, mean, std))

                # Indexing time for every 1/sf seconds

                cur_time = (int) (time.time())
                file_time = cur_time - initialtime # Time for each data in seconds

                for i in range(self.samples):
                    self.time_memory[i] = file_time + self.time_index[i]
                    f.write("{0} {1} {2} {3}\n".format(self.time_memory[i], x_val[i], y_val[i], z_val[i])) # writing it in data file

                self.time_memory[i] += file_time
                self.t.extend(self.time_memory)
                self.xar.extend(x_val)
                self.yar.extend(y_val)
                self.zar.extend(z_val)
                self.emit(QtCore.SIGNAL('InputUpdate'), (self.t, self.xar, self.yar, self.zar)) #Sending a signal to GUI
                f.flush()

    def readvalues(self):

        data = self.task.read(self.samples, fill_mode='group_by_channel')
        dat = np.asarray(data) #dat is a 2-D array which consists of three 1D array (x, y, z)
        if self.check == True: #Connected to fluxgate checkbutton / If it is True, converts from Voltage to nano Tesla.
            k = 7000
        else:
            k = 1

        x_val = k*dat[0]
        y_val = k*dat[1]
        z_val = k*dat[2]

        return x_val, y_val, z_val

    def stop(self):
            self.task.stop()
            self.task.clear()




