#!/usr/bin/env python3
from PyQt5 import QtWidgets, uic, QtCore, QtGui
import pickle
import sys, os
from dmx import Colour, DMXLight, DMXInterface, DMXLight3Slot, DMXUniverse

PRESET_FILE = "presets.pkl"

class Preset(object):

    def __init__(self, gui):
        self.l_r = gui.left_r.value()
        self.l_g = gui.left_g.value()
        self.l_b = gui.left_b.value()
        self.r_r = gui.right_r.value()
        self.r_g = gui.right_g.value()
        self.r_b = gui.right_b.value()

        self.name = gui.preset_name.text()
        self.link = gui.link.isChecked()

    def __str__(self):
        return("%s : %s. [%s %s %s] [%s %s %s]" % (self.name, self.link, self.l_r, self.l_g, self.l_b, self.r_r, self.r_g, self.r_b))

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(self.__class__, self).__init__()

        uic.loadUi('lights/mainwindow.ui', self)
        self.setWindowTitle("DMX")
        self.setWindowIcon(QtGui.QIcon("icon.png"));

        self.load_presets()

        self.left_r.valueChanged.connect(lambda: self.update_lights())
        self.left_g.valueChanged.connect(lambda: self.update_lights())
        self.left_b.valueChanged.connect(lambda: self.update_lights())
        self.right_r.valueChanged.connect(lambda: self.update_lights())
        self.right_g.valueChanged.connect(lambda: self.update_lights())
        self.right_b.valueChanged.connect(lambda: self.update_lights())

        # mem buttons
        self.button_add.clicked.connect(self.add_preset)
        self.button_delete.clicked.connect(self.delete_preset)
        self.button_update.clicked.connect(self.update_preset)
    
        self.preset_name.textChanged.connect(self.preset_name_changed)
        self.preset_list.currentIndexChanged.connect(self.preset_changed)
        self.preset_list.activated.connect(self.preset_changed)

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
            print("setting up 1 x 3 channel light at address %d" % address)
            light = DMXLight3Slot(address=address)
            self.universe.add_light(light)
            self.lights.append(light)

        self.update_lights()

    def preset_name_changed(self, text):
        if text:
            self.button_add.setEnabled(True)
            self.button_update.setEnabled(True)
        else:
            self.button_add.setEnabled(False)

    def preset_changed(self, index):
        if index == -1:
            print("no preset")
            return

        print("change preset to %d" % index)
        preset = self.presets[index]
        self.button_update.setEnabled(False)
        print(preset)

        self.link.setChecked(preset.link)
        self.left_r.setValue(preset.l_r);
        self.left_g.setValue(preset.l_g);
        self.left_b.setValue(preset.l_b);

        self.right_r.setValue(preset.r_r);
        self.right_g.setValue(preset.r_g);
        self.right_b.setValue(preset.r_b);

        self.preset_name.setText(preset.name)

    def load_presets(self):
        try:
            with open(PRESET_FILE, 'rb') as fh:
                self.presets = pickle.load(fh)
                self.update_preset_combo_box()
        except FileNotFoundError as e:
            self.presets = []

        if len(self.presets):
            self.button_delete.setEnabled(True)
            # force load of preset
            self.preset_changed(0)

    def update_preset_combo_box(self):
        self.preset_list.clear()
        for preset in self.presets:
            self.preset_list.addItem(preset.name)

    def save_presets(self):
        print("save presets")
        with open(PRESET_FILE, 'wb') as fh:
            pickle.dump(self.presets, fh)
        
    def add_preset(self):
        preset = Preset(self)
        self.presets.append(preset)
        self.preset_list.addItem(preset.name)
        self.preset_list.setCurrentIndex(self.presets.index(preset))

    def delete_preset(self):
        index = self.preset_list.currentIndex()
        print("removing %s at index %d" % (self.preset_list.currentText(), index))
        del(self.presets[index])
        self.preset_list.removeItem(index)
        
        if not len(self.presets):
            self.button_delete.setEnabled(False)

    def update_preset(self):
        index = self.preset_list.currentIndex()
        preset = Preset(self)
        # overwrite
        self.presets[index] = preset
        print(self.presets[index])
        self.update_preset_combo_box()

    def update_lights(self):
        self.button_update.setEnabled(True)

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


    def closeEvent(self, event):
        self.save_presets()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
