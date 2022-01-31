#!/usr/bin/env python3
from PyQt5 import QtWidgets, uic, QtCore, QtGui
import sys, os
from dmx import Colour, DMXLight, DMXInterface, DMXLight3Slot, DMXUniverse

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(self.__class__, self).__init__()

        uic.loadUi('lights/mainwindow.ui', self)
        self.setWindowTitle("DMX")
        self.setWindowIcon(QtGui.QIcon("icon.png"));

        self.left_r.valueChanged.connect(lambda: self.update_lights())
        self.left_g.valueChanged.connect(lambda: self.update_lights())
        self.left_b.valueChanged.connect(lambda: self.update_lights())
        self.right_r.valueChanged.connect(lambda: self.update_lights())
        self.right_g.valueChanged.connect(lambda: self.update_lights())
        self.right_b.valueChanged.connect(lambda: self.update_lights())

        # mem buttons
        self.mem_z2a.clicked.connect(lambda: self.load("z2a"))
        self.mem_yosys.clicked.connect(lambda: self.load("yosys"))
        self.mem_red.clicked.connect(lambda: self.load("red"))
        self.init_cam.clicked.connect(lambda: self.init_camera())

        # dmx updates
        self.dmx_timer = QtCore.QTimer(self)
        self.dmx_timer.start(10) 
        self.dmx_timer.timeout.connect(self.update_dmx)

        # dmx interface setup with PyDMX
        self.interface = DMXInterface("FT232R")
        self.universe = DMXUniverse()

        # 2 x 24 channel lights chained, with first starting at address 1 and 2nd at 25
        # in 24 channel mode, have 8 segments with R, G and B.
        self.num_chan = 48
        self.num_segs = self.num_chan / 3

        self.lights = []
        # Define DMX lights
        for address in range(1, self.num_chan, 3):
#            print("setting up 1 x 3 channel light at address %d" % address)
            light = DMXLight3Slot(address=address)
            self.universe.add_light(light)
            self.lights.append(light)

    def init_camera(self):
        print("init cam")
        webcamdevice="/dev/video0"
        cam_settings = {
            'power_line_frequency': 1,
            'exposure_auto': 1,
            'gain' : 5,
            'white_balance_temperature_auto': 0,
            'white_balance_temperature' : 5000,
            'exposure_absolute': 400,
        }
        for key, value in cam_settings.items():
            print("setting %s to %d" % (key, value))
            os.system("v4l2-ctl -d %s --set-ctrl=%s=%d" % (webcamdevice, key, value))

    def load(self, mem):
        if(mem == 'z2a'):
            self.link.setChecked(0)

            self.left_r.setValue(0);
            self.left_g.setValue(0);
            self.left_b.setValue(100);

            self.right_r.setValue(0);
            self.right_g.setValue(117);
            self.right_b.setValue(18);

        if(mem == 'yosys'):
            self.link.setChecked(0)
            self.left_r.setValue(180);
            self.left_g.setValue(0);
            self.left_b.setValue(44);

            self.right_r.setValue(24);
            self.right_g.setValue(0);
            self.right_b.setValue(96);

        if(mem == 'red'):
            self.link.setChecked(1)
            self.left_r.setValue(255);
            self.left_g.setValue(0);
            self.left_b.setValue(0);

    def update_lights(self):
        if self.link.isChecked():
            self.right_r.setValue(self.left_r.value())
            self.right_g.setValue(self.left_g.value())
            self.right_b.setValue(self.left_b.value())

        # interpolate from left to right across all lights
        for num, light in enumerate(reversed(self.lights)):
            R = int(self.left_r.value() - num * ((self.left_r.value() - self.right_r.value()))/(self.num_segs-1))
            G = int(self.left_g.value() - num * ((self.left_g.value() - self.right_g.value()))/(self.num_segs-1))
            B = int(self.left_b.value() - num * ((self.left_b.value() - self.right_b.value()))/(self.num_segs-1))
            #print(num, R, G, B)
            light.set_colour(Colour(R,G,B))

    def update_dmx(self):
        self.interface.set_frame(self.universe.serialise())
        self.interface.send_update()


if __name__ == '__main__':
    """
    parser = argparse.ArgumentParser(description="View Events")
    parser.add_argument('--listing', help="load a Vallen CSV listing", action='store')
    parser.add_argument('--db-file', help="load a Vallen DB (sqlite containing raw data)", action='store')
    parser.add_argument('--channels', help="comma separated list of 4 channels: R1,R2,L1,L2", action='store', default="1,2,3,4")
    parser.add_argument('--sensor-distances', help="comma separated list left and right sensor distances: RW,LW", action='store')
    parser.add_argument('--calibrate', help="run calibrate at start", action="store_const", const=True)
    parser.add_argument('--locate', help="run locate at start", action="store_const", const=True)
    parser.add_argument('--tab', help="switch to this tab after startup (0 index)", action="store")
    args = parser.parse_args()
    """

    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
