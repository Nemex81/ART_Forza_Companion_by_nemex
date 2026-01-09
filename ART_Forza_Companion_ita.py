import pygame
from pydub import AudioSegment
from pydub.playback import play
import io
import socket
import struct
import math
import accessible_output2.outputs.auto
import threading
import concurrent.futures
import time
import json
import os
import sys



#def resource_path(relative_path):
#    """ Risolve i percorsi delle risorse per eseguibili e sviluppo """
    #if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        #base_path = sys._MEIPASS
    #else:
        #base_path = os.path.abspath(".")
    #return os.path.join(base_path, relative_path)

# Inizializzazione del mixer Pygame
pygame.mixer.init()

# Variabili di configurazione
bmMonitor = False
prePitch = 0
preRoll = 0
armedBenchmark = False
startBenchmark = False
bmSpeed = 60
bmStartTime = 0
bmEndTime = 0
speedInterval = 5
curSpeedInt = 0
preSpeed = 0
speedSense = 10
packeting = True
sound_events = {}
packed_data = []
preGear = 0
bottomedFL = False
bottomedFR = False
bottomedRL = False
bottomedRR = False
maxTF = 200
maxTR = 200
frontMax = False
rearMax = False
preTTFL = 0
preTTFR = 0
preTTRL = 0
preTTRR = 0
preSuspFL = 0
preSuspFR = 0
preSuspRL = 0
preSuspRR = 0
metric = False
metricString = "km/h" if metric else "MPH"
speakingTemp = False
speakingSusp = False
speakingGear = False
speakingCompass = False
speakingElevation = False
speakingSpeed = False
last_executed = {}
o = accessible_output2.outputs.auto.Auto()
audioCompass = False
compassClicks = False
speedMon = False
elevationSensor = False
suspAudio = False
tempAudio = False
gearAudio = False
preYaw = 0.0
preDir = ""
preClick = 0.0
exceed = 0
preElevation = 0
elevationSense = 3
compassSense = 10

configuration_values = {
    "Speed Interval": speedInterval,
    "Speed Sensitivity": speedSense,
    "Compass Sensitivity": compassSense,
    "Elevation Sensitivity": elevationSense,
    "Front Tire Temp": maxTF,
    "Rear Tire Temp": maxTR,
    "Benchmark Speed": bmSpeed
}

def save_configuration(dict1, dict2, int_value):
    current_directory = os.getcwd()
    file_path = os.path.join(current_directory, "config.json")

    config_data = {
        "dict1": dict1,
        "dict2": dict2,
        "int_value": int_value
    }

    with open(file_path, 'w') as config_file:
        json.dump(config_data, config_file)
    speak("Configurazione salvata.")

def load_configuration():
    current_directory = os.getcwd()
    file_path = os.path.join(current_directory, "config.json")

    try:
        with open(file_path, 'r') as config_file:
            config_data = json.load(config_file)
            dict1 = config_data.get("dict1", {})
            dict2 = config_data.get("dict2", {})
            int_value = config_data.get("int_value", 0)
            return dict1, dict2, int_value
    except FileNotFoundError:
        return {label: False for label in [
            "Speed Audio Toggle", "Elevation Audio Toggle", "Suspension Audio Toggle",
            "Tire Temp Audio Toggle", "SR Speed Toggle", "SR Elevation Toggle",
            "SR Compass Toggle", "SR Suspension Toggle", "SR Tire Temps Toggle",
            "SR Gears Toggle", "Measurement Toggle", "Benchmark Toggle", "Save Configuration"
        ]}, {
            "Speed Interval": None,
            "Speed Sensitivity": None,
            "Elevation Sensitivity": None,
            "Compass Sensitivity": None,
            "Front Tire Temp": None,
            "Rear Tire Temp": None,
            "Benchmark Speed": None
        }, 0

from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton, QComboBox, QLineEdit, QLabel
from PyQt5.QtGui import QIntValidator

audio_compass_options = ['Disattivato', 'Direzioni cardinali', 'Solo clic', 'Direzioni e clic']
audio_compass_selection = 0

button_states = {label: False for label in [
    "Speed Audio Toggle", "Elevation Audio Toggle", "Suspension Audio Toggle",
    "Tire Temp Audio Toggle", "SR Speed Toggle", "SR Elevation Toggle",
    "SR Compass Toggle", "SR Suspension Toggle", "SR Tire Temps Toggle",
    "SR Gears Toggle", "Measurement Toggle", "Benchmark Toggle", "Save Configuration"
]}

value_variables = {
    "Speed Interval": None,
    "Speed Sensitivity": None,
    "Elevation Sensitivity": None,
    "Compass Sensitivity": None,
    "Front Tire Temp": None,
    "Rear Tire Temp": None,
    "Benchmark Speed": None
}

labels_mapping = {
    "Speed Audio Toggle": "Attiva Audio Velocità",
    "Elevation Audio Toggle": "Attiva Audio Altitudine",
    "Suspension Audio Toggle": "Attiva Audio Sospensioni",
    "Tire Temp Audio Toggle": "Attiva Audio Temperatura",
    "SR Speed Toggle": "Lettura Velocità",
    "SR Elevation Toggle": "Lettura Altitudine",
    "SR Compass Toggle": "Lettura Bussola",
    "SR Suspension Toggle": "Lettura Sospensioni",
    "SR Tire Temps Toggle": "Lettura Temperature",
    "SR Gears Toggle": "Lettura Marce",
    "Measurement Toggle": "Unità di Misura",
    "Benchmark Toggle": "Avvia Benchmark",
    "Save Configuration": "Salva Configurazione"
}

edit_labels_mapping = {
    "Speed Interval": "Intervallo Velocità (MPH/kmh)",
    "Speed Sensitivity": "Sensibilità Velocità",
    "Elevation Sensitivity": "Sensibilità Altitudine (m)",
    "Compass Sensitivity": "Sensibilità Bussola (gradi)",
    "Front Tire Temp": "Temp. Max Anteriore (°C)",
    "Rear Tire Temp": "Temp. Max Posteriore (°C)",
    "Benchmark Speed": "Velocità Benchmark (MPH/kmh)"
}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Assistente Accessibile per Forza Motorsport")
        self.setGeometry(100, 100, 600, 500)
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        self.add_audio_panel()
        self.add_edit_panel()

    def add_audio_panel(self):
        panel = QWidget()
        layout = QVBoxLayout()

        for eng_label, ita_label in labels_mapping.items():
            button = QPushButton(ita_label)
            button.clicked.connect(lambda checked, label=eng_label: self.toggle_button(label))
            layout.addWidget(button)

        self.global_combo_audio_compass = QComboBox()
        self.global_combo_audio_compass.addItems(audio_compass_options)
        self.global_combo_audio_compass.currentIndexChanged.connect(self.audio_compass_changed)
        layout.addWidget(self.global_combo_audio_compass)

        panel.setLayout(layout)
        self.tab_widget.addTab(panel, "Audio & Opzioni")

    def toggle_button(self, label):
        global button_states, configuration_values, audio_compass_selection
        if label == "Benchmark Toggle" and not button_states[label]:
            button_states[label] = True
            speak("Preparazione benchmark: portare la velocità a 0 e il motore al minimo")
        elif label == "Benchmark Toggle" and button_states[label]:
            button_states[label] = False
            speak("Benchmark annullato")
        elif label == "Save Configuration":
            save_configuration(button_states, configuration_values, audio_compass_selection)
        else:
            button_states[label] = not button_states[label]
            stato = "attivato" if button_states[label] else "disattivato"
            speak(f"{labels_mapping[label]} {stato}")

    def audio_compass_changed(self, index):
        global audio_compass_selection
        audio_compass_selection = index
        speak(f"Modalità bussola audio: {audio_compass_options[index]}")

    def add_edit_panel(self):
        panel = QWidget()
        layout = QVBoxLayout()

        for eng_label, ita_label in edit_labels_mapping.items():
            hbox = QVBoxLayout()
            lbl = QLabel(ita_label)
            edit = QLineEdit()
            edit.setValidator(QIntValidator(0, 1000))
            value_variables[eng_label] = edit
            hbox.addWidget(lbl)
            hbox.addWidget(edit)
            layout.addLayout(hbox)

        submit_button = QPushButton("Applica Impostazioni")
        submit_button.clicked.connect(self.submit_values)
        layout.addWidget(submit_button)

        panel.setLayout(layout)
        self.tab_widget.addTab(panel, "Impostazioni Sensibilità")

    def submit_values(self):
        global value_variables
        error = False
        for eng_label, edit in value_variables.items():
            if edit.text().isdigit():
                configuration_values[eng_label] = int(edit.text())
            elif edit.text() != "":
                error = True
        speak("Impostazioni applicate" if not error else "Valori non validi")

def mainStart():
    if __name__ == '__main__':
        app = QApplication([])
        main_window = MainWindow()
        main_window.show()
        app.exec_()

def updateVars():
    global configuration_values, speedInterval, speedSense, elevationSense, compassSense, maxTF, maxTR, bmSpeed
    global metric, speakingTemp, speakingSusp, speakingGear, speakingCompass, speakingElevation, speakingSpeed
    global audioCompass, compassClicks, speedMon, elevationSensor, suspAudio, tempAudio, button_states, metricString
    
    configuration_values = {key: int(value.text()) if value.text().isdigit() else configuration_values[key] 
                          for key, value in value_variables.items()}
    
    speedInterval = configuration_values["Speed Interval"]
    speedSense = configuration_values["Speed Sensitivity"]
    elevationSense = configuration_values["Elevation Sensitivity"]
    compassSense = configuration_values["Compass Sensitivity"]
    maxTF = configuration_values["Front Tire Temp"]
    maxTR = configuration_values["Rear Tire Temp"]
    bmSpeed = configuration_values["Benchmark Speed"]
    
    metric = button_states["Measurement Toggle"]
    metricString = "km/h" if metric else "MPH"
    
    speakingTemp = button_states["SR Tire Temps Toggle"]
    speakingSusp = button_states["SR Suspension Toggle"]
    speakingGear = button_states["SR Gears Toggle"]
    speakingCompass = button_states["SR Compass Toggle"]
    speakingElevation = button_states["SR Elevation Toggle"]
    speakingSpeed = button_states["SR Speed Toggle"]
    
    audioCompass = audio_compass_selection in [1,3]
    compassClicks = audio_compass_selection in [2,3]
    
    speedMon = button_states["Speed Audio Toggle"]
    elevationSensor = button_states["Elevation Audio Toggle"]
    suspAudio = button_states["Suspension Audio Toggle"]
    tempAudio = button_states["Tire Temp Audio Toggle"]
    
    if not button_states["Benchmark Toggle"]:
        global armedBenchmark, startBenchmark
        armedBenchmark = startBenchmark = False

def speak(text, interrupt=True):
    o.output(text, interrupt)

def print_Speak(speaking, message):
    print(message)
    if speaking:
        speak(message, interrupt=False)

def execute_After(func, interval):
    current_time = time.time()
    if func not in last_executed or current_time - last_executed[func] >= interval:
        last_executed[func] = current_time
        timer = threading.Timer(interval, func)
        timer.start()

def load_sound(file_path):
    return AudioSegment.from_file(file_path)

def set_stereo_panning(sound, panning):
    return sound.pan(panning)

def set_pitch(sound, pitch):
    new_sample_rate = int(sound.frame_rate * (2 ** pitch))
    return sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})

def set_volume(sound, volume):
    return sound + volume

#sound = load_sound(resource_path("beep.wav"))
#speed = load_sound(resource_path("speed.wav"))
#click = load_sound(resource_path("click.wav"))
#ascend = load_sound(resource_path("ascend.wav"))
#descend = load_sound(resource_path("descend.wav"))
#temp = load_sound(resource_path("temp.wav"))
#susp = load_sound(resource_path("susp.wav"))

sound = load_sound("beep.wav")
speed = load_sound("speed.wav")
click = load_sound("click.wav")
ascend = load_sound("ascend.wav")
descend = load_sound("descend.wav")
temp = load_sound("temp.wav")
tempR = load_sound("temp.wav")
tempR = set_pitch(temp, -1)
susp = load_sound("susp.wav")
Suspfl = load_sound("susp.wav")
Suspfr = load_sound("susp.wav")
Susprl = load_sound("susp.wav")
Susprr = load_sound("susp.wav")
Suspfl = set_stereo_panning(Suspfl,-1)
Suspfr = set_stereo_panning(Suspfr,1)
Susprl = set_stereo_panning(Susprl,-1)
Susprl = set_pitch(Susprl, -1)
Susprr = set_stereo_panning(Susprr,1)
Susprr = set_pitch(Susprr, -1)

def export_and_load(sound):
    buffer = io.BytesIO()
    sound.export(buffer, format="wav")
    buffer.seek(0)
    loadedSound = pygame.mixer.Sound(buffer)
    buffer.close()
    return loadedSound

speed = export_and_load(speed)
ascend = export_and_load(ascend)
descend = export_and_load(descend)
temp = export_and_load(temp)
tempR = export_and_load(tempR)
susp = export_and_load(susp)
Suspfl = export_and_load(Suspfl)
Suspfr = export_and_load(Suspfr)
Susprl = export_and_load(Susprl)
Susprr = export_and_load(Susprr)

def ash(masterSound, heading):
    sound = masterSound
    panning = (heading - 180) / 90
    if panning > 1:
        panning = -2 + panning
    elif panning < -1:
        panning = 2 + panning

    if 270 > heading > 90:
        panning = -panning

    sound = sound.pan(panning)
    
    pitch=0
    if heading > 270:
        pitch= (heading-270)/90
    if heading > 180 and heading < 270:
        pitch= -1+((heading-180)/90)
    if heading > 90 and heading < 180:
        pitch = 1-(heading/90)
    if heading > 0 and heading < 90:
        pitch = 1-(heading/90)
    if heading == 270 or heading == 90:
        pitch=0
    if heading == 0:
        pitch=1
    if heading == 180:
        pitch =-1
    return set_pitch(sound, pitch)

def preload_compass_sounds(master_sound):
    compass_sounds = []
    for heading in range(360):
        adjusted_sound = ash(master_sound, heading)
        sound_handle = export_and_load(adjusted_sound)
        compass_sounds.append(sound_handle)
    return compass_sounds

clickSounds = preload_compass_sounds(click)
compassSounds = preload_compass_sounds(sound)

def sound_thread_function(sound_name, soundHandle, index=None):
    if index is not None:
        threadSound = soundHandle[index]
    else:
        threadSound = soundHandle

    while True:
        sound_events[sound_name].wait()
        threadSound.play()
        sound_events[sound_name].clear()

def create_sound_thread(sound_name, soundHandle):
    if isinstance(soundHandle, list):
        for index, single_sound in enumerate(soundHandle):
            sound_events[f"{sound_name}_{index}"] = threading.Event()
            thread = threading.Thread(target=sound_thread_function, args=(f"{sound_name}_{index}", soundHandle, index))
            thread.daemon = True
            thread.start()
    else:
        sound_events[sound_name] = threading.Event()
        thread = threading.Thread(target=sound_thread_function, args=(sound_name, soundHandle))
        thread.daemon = True
        thread.start()

def addSound(sound_name, index=None):
    if index is not None:
        sound_events[f"{sound_name}_{index}"].set()
    else:
        sound_events[sound_name].set()

def convertDir(degrees):
    if 337.5 <= degrees < 360 or 0 <= degrees < 22.5:
        return "Nord"
    elif 22.5 <= degrees < 67.5:
        return "Nord-Est"
    elif 67.5 <= degrees < 112.5:
        return "Est"
    elif 112.5 <= degrees < 157.5:
        return "Sud-Est"
    elif 157.5 <= degrees < 202.5:
        return "Sud"
    elif 202.5 <= degrees < 247.5:
        return "Sud-Ovest"
    elif 247.5 <= degrees < 292.5:
        return "Ovest"
    elif 292.5 <= degrees < 337.5:
        return "Nord-Ovest"
    else:
        return "Direzione non valida"

def speedConvert(speed_mps):
    return speed_mps * 3.6 if metric else speed_mps * 2.23694

def speedBenchMark(curRPM, idleRPM, curSpeed, curTime):
    global button_states, bmMonitor, armedBenchmark, bmStartTime, bmEndTime, startBenchmark, bmSpeed
    speed = speedConvert(curSpeed)
    
    if bmMonitor:
        if not armedBenchmark and round(curRPM) == round(idleRPM) and round(speed) == 0:
            armedBenchmark = True
            print("Pronto per benchmark")
            
        if armedBenchmark and curRPM != idleRPM and not startBenchmark:
            startBenchmark = True
            bmStartTime = curTime
            print("Timer avviato")
            
        if armedBenchmark and startBenchmark and speed >= bmSpeed:
            bmMonitor = False
            button_states["Benchmark Toggle"] = False
            armedBenchmark = startBenchmark = False
            bmEndTime = curTime
            bmTotalTime = (bmEndTime - bmStartTime)/1000
            print_Speak(True, f"{bmSpeed} {metricString} raggiunte in {bmTotalTime:.1f} secondi")

port = 5300
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('', port))
server_socket.settimeout(1)
print(f"In ascolto su porta {port}")

def packetReceiver():
    global packed_data, packeting
    while packeting:
        try:
            data, addr = server_socket.recvfrom(332)
            format_string = 'iI27f4i20f5i17fH6B4bfi'
            if len(data) >= 0:
                packed_data = struct.unpack(format_string, data[:struct.calcsize(format_string)])
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Errore: {e}")
            break
        speedBenchMark(packed_data[4], packed_data[3], packed_data[61], packed_data[1])

def processPacket():
    unpacked_data = packed_data
    
    # Elaborazione dati
    curGear = unpacked_data[81]
    if curGear != preGear:
        if curGear == 0:
            print_Speak(speakingGear, "Retro")
        elif curGear != 11:
            print_Speak(speakingGear, f"Marcia {curGear}")
        preGear = curGear
    
    # Temperatura pneumatici
    TTFL, TTFR = unpacked_data[64], unpacked_data[65]
    if TTFL >= maxTF or TTFR >= maxTF:
        print_Speak(speakingTemp, f"Temperatura anteriore critica: {TTFL}° | {TTFR}°")
    
    # Sospensioni
    suspFL = unpacked_data[17]
    if suspFL >= 1 and not bottomedFL:
        print_Speak(speakingSusp, "Sospensione anteriore sinistra al limite")
    
    # Altitudine
    curElevation = unpacked_data[59]
    if abs(curElevation - preElevation) >= elevationSense:
        if curElevation > preElevation:
            print_Speak(speakingElevation, "Salita")
        else:
            print_Speak(speakingElevation, "Discesa")
        preElevation = curElevation
    
    # Velocità
    curSpeed = speedConvert(unpacked_data[61])
    if abs(curSpeed - preSpeed) >= speedSense:
        print_Speak(speakingSpeed, f"{int(curSpeed)} {metricString}")
        preSpeed = curSpeed

def shutDown():
    print("Arresto del server...")
    pygame.mixer.quit()
    packeting = False
    server_socket.close()
    packetThread.join()

# Avvio applicazione
mainThread = threading.Thread(target=mainStart)
packetThread = threading.Thread(target=packetReceiver)
button_states, value_variables, audio_compass_selection = load_configuration()

try:
    packetThread.start()
    mainThread.start()
    
    # Inizializzazione suoni
    create_sound_thread('ascend', ascend)
    create_sound_thread('descend', descend)
    create_sound_thread('front temp', temp)
    create_sound_thread('rear temp', tempR)
    create_sound_thread('Suspfl', Suspfl)
    create_sound_thread('Suspfr', Suspfr)
    create_sound_thread('Susprl', Susprl)
    create_sound_thread('Susprr', Susprr)
    create_sound_thread('speed', speed)
    create_sound_thread('click', clickSounds)
    create_sound_thread('compass', compassSounds)

    # Main loop
    while True:
        updateVars()
        if packed_data:
            processPacket()
        time.sleep(0.05)
        
except KeyboardInterrupt:
    shutDown()