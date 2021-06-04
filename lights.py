#!/usr/bin/env python3
from PyQt5 import QtWidgets, uic, QtCore, QtGui
import sys
from dmx import Colour, DMXLight, DMXInterface, DMXLight3Slot, DMXUniverse

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(self.__class__, self).__init__()

        uic.loadUi('lights/mainwindow.ui', self)
        self.setWindowTitle("DMX")

        self.left_r.valueChanged.connect(lambda: self.update_lights())
        self.left_g.valueChanged.connect(lambda: self.update_lights())
        self.left_b.valueChanged.connect(lambda: self.update_lights())
        self.right_r.valueChanged.connect(lambda: self.update_lights())
        self.right_g.valueChanged.connect(lambda: self.update_lights())
        self.right_b.valueChanged.connect(lambda: self.update_lights())

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

    def update_lights(self):
        if self.link.isChecked():
            self.right_r.setValue(self.left_r.value())
            self.right_g.setValue(self.left_g.value())
            self.right_b.setValue(self.left_b.value())

        # interpolate from left to right across all lights
        for num, light in enumerate(self.lights):
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
