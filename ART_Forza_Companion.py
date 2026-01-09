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
import locale
pygame.mixer.init()
# i18n helpers
translations = {}
current_language = None
language_preference = None
SUPPORTED_LANGUAGES = {"en", "it"}

def detect_system_language():
	default_locale = locale.getdefaultlocale()
	lang_code = default_locale[0] if default_locale and default_locale[0] else ""
	if isinstance(lang_code, str) and lang_code.lower().startswith("it"):
		return "it"
	return "en"

def load_translations(lang=None):
	global translations
	global current_language
	base_lang = lang if lang in SUPPORTED_LANGUAGES else detect_system_language()
	current_language = base_lang
	current_directory = os.getcwd()
	fallback_path = os.path.join(current_directory, "localization", "en.json")
	lang_path = os.path.join(current_directory, "localization", f"{base_lang}.json")
	try:
		with open(fallback_path, 'r', encoding="utf-8") as f:
			translations = json.load(f)
	except FileNotFoundError:
		translations = {}
	if base_lang != "en":
		try:
			with open(lang_path, 'r', encoding="utf-8") as f:
				translations.update(json.load(f))
		except FileNotFoundError:
			pass

def tr(key, **kwargs):
	value = translations.get(key, key)
	try:
		return str(value).format(**kwargs)
	except Exception:
		return value

load_translations()
TOGGLE_KEYS = [
	"toggle.audio.speed",
	"toggle.audio.elevation",
	"toggle.audio.suspension",
	"toggle.audio.tire_temp",
	"toggle.sr.speed",
	"toggle.sr.elevation",
	"toggle.sr.compass",
	"toggle.sr.suspension",
	"toggle.sr.tire_temps",
	"toggle.sr.gears",
	"toggle.measurement.metric",
	"toggle.benchmark",
	"action.config.save"
]

SETTING_KEYS = [
	"setting.speed.interval",
	"setting.speed.sensitivity",
	"setting.compass.sensitivity",
	"setting.elevation.sensitivity",
	"setting.tire_temp.front_max",
	"setting.tire_temp.rear_max",
	"setting.benchmark.target_speed"
]

AUDIO_COMPASS_OPTION_KEYS = [
	"option.audio_compass.off",
	"option.audio_compass.cardinals",
	"option.audio_compass.clicks",
	"option.audio_compass.both"
]

LANGUAGE_OPTIONS = [("en", "option.language.en"), ("it", "option.language.it")]

OLD_TOGGLE_KEY_MAP = {
	"Speed Audio Toggle": "toggle.audio.speed",
	"Elevation Audio Toggle": "toggle.audio.elevation",
	"Suspension Audio Toggle": "toggle.audio.suspension",
	"Tire Temp Audio Toggle": "toggle.audio.tire_temp",
	"SR Speed Toggle": "toggle.sr.speed",
	"SR Elevation Toggle": "toggle.sr.elevation",
	"SR Compass Toggle": "toggle.sr.compass",
	"SR Suspension Toggle": "toggle.sr.suspension",
	"SR Tire Temps Toggle": "toggle.sr.tire_temps",
	"SR Gears Toggle": "toggle.sr.gears",
	"Measurement Toggle": "toggle.measurement.metric",
	"Benchmark Toggle": "toggle.benchmark",
	"Save Configuration": "action.config.save"
}

OLD_SETTING_KEY_MAP = {
	"Speed Interval": "setting.speed.interval",
	"Speed Sensitivity": "setting.speed.sensitivity",
	"Compass Sensitivity": "setting.compass.sensitivity",
	"Elevation Sensitivity": "setting.elevation.sensitivity",
	"Front Tire Temp": "setting.tire_temp.front_max",
	"Rear Tire Temp": "setting.tire_temp.rear_max",
	"Benchmark Speed": "setting.benchmark.target_speed"
}

# Variables
DEFAULT_SPEED_INTERVAL = 5
DEFAULT_SPEED_SENSITIVITY = 10
DEFAULT_COMPASS_SENSITIVITY = 10
DEFAULT_ELEVATION_SENSITIVITY = 3
DEFAULT_FRONT_TIRE_TEMP = 200
DEFAULT_REAR_TIRE_TEMP = 200
DEFAULT_BENCHMARK_SPEED = 60

bmMonitor=False
prePitch= 0
preRoll = 0
armedBenchmark=False
startBenchmark = False
bmSpeed = DEFAULT_BENCHMARK_SPEED
bmStartTime= 0
bmEndTime = 0
speedInterval = DEFAULT_SPEED_INTERVAL
curSpeedInt = 0
preSpeed = 0
speedSense= DEFAULT_SPEED_SENSITIVITY
packeting = True
sound_events = {}
packed_data = []
preGear = 0
bottomedFL = False
bottomedFR = False
bottomedRL = False
bottomedRR = False
maxTF = DEFAULT_FRONT_TIRE_TEMP
maxTR = DEFAULT_REAR_TIRE_TEMP
frontMax = False
rearMax = False
preTTFL=0
preTTFR = 0
preTTRL = 0
preTTRR = 0
preSuspFL = 0
preSuspFR = 0
preSuspRL = 0
preSuspRR = 0
metric=False
metricString= "MPH"
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
preYaw= 0.0
preDir=""
preClick=0.0
exceed=0
preElevation=0
elevationSense=DEFAULT_ELEVATION_SENSITIVITY
compassSense=DEFAULT_COMPASS_SENSITIVITY

def default_configuration_values():
	return {
		"setting.speed.interval": DEFAULT_SPEED_INTERVAL,
		"setting.speed.sensitivity": DEFAULT_SPEED_SENSITIVITY,
		"setting.compass.sensitivity": DEFAULT_COMPASS_SENSITIVITY,
		"setting.elevation.sensitivity": DEFAULT_ELEVATION_SENSITIVITY,
		"setting.tire_temp.front_max": DEFAULT_FRONT_TIRE_TEMP,
		"setting.tire_temp.rear_max": DEFAULT_REAR_TIRE_TEMP,
		"setting.benchmark.target_speed": DEFAULT_BENCHMARK_SPEED
	}

configuration_values = default_configuration_values()
def save_configuration(dict1, dict2, int_value, language=None):
	current_directory = os.getcwd()
	file_path = os.path.join(current_directory, "config.json")

	config_data = {
		"dict1": dict1,
		"dict2": dict2,
		"int_value": int_value
	}
	if language in SUPPORTED_LANGUAGES:
		config_data["language"] = language

	with open(file_path, 'w') as config_file:
		json.dump(config_data, config_file)
	speak(tr("tts.config_saved"))

def _normalize_setting_value(key, value):
	defaults = default_configuration_values()
	try:
		return int(value)
	except (ValueError, TypeError):
		return defaults.get(key, value)

# Function to read and update configuration from a file
def load_configuration():
	current_directory = os.getcwd()
	file_path = os.path.join(current_directory, "config.json")

	toggle_defaults = {key: False for key in TOGGLE_KEYS}
	setting_defaults = default_configuration_values()
	audio_compass_value = 0
	language_pref = None

	try:
		with open(file_path, 'r') as config_file:
			config_data = json.load(config_file)
			dict1 = config_data.get("dict1", {})
			dict2 = config_data.get("dict2", {})
			int_value = config_data.get("int_value", 0)
			language_value = config_data.get("language")
			if isinstance(language_value, str) and language_value.lower() in SUPPORTED_LANGUAGES:
				language_pref = language_value.lower()

			for key, value in dict1.items():
				new_key = OLD_TOGGLE_KEY_MAP.get(key, key)
				if new_key in toggle_defaults:
					toggle_defaults[new_key] = bool(value)

			for key, value in dict2.items():
				new_key = OLD_SETTING_KEY_MAP.get(key, key)
				if new_key in setting_defaults:
					setting_defaults[new_key] = _normalize_setting_value(new_key, value)

			try:
				audio_compass_value = int(int_value)
			except (TypeError, ValueError):
				audio_compass_value = 0
			return toggle_defaults, setting_defaults, audio_compass_value, language_pref
	except FileNotFoundError:
		return toggle_defaults, setting_defaults, audio_compass_value, language_pref  # Return default values if the file doesn't exist

from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton, QComboBox, QLineEdit, QLabel
from PyQt5.QtGui import QIntValidator

# Define global variables
audio_compass_options = AUDIO_COMPASS_OPTION_KEYS
audio_compass_selection = 0

button_states = {label: False for label in TOGGLE_KEYS}

value_variables = default_configuration_values()

class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()

		self.setWindowTitle(tr("ui.app_title"))
		self.setGeometry(100, 100, 600, 500)

		self.tab_widget = QTabWidget()
		self.setCentralWidget(self.tab_widget)

		self.add_audio_panel()
		self.add_edit_panel()

	def add_audio_panel(self):
		panel = QWidget()
		layout = QVBoxLayout()

		lang_label = QLabel(tr("ui.language"))
		self.language_combo = QComboBox()
		for code, key in LANGUAGE_OPTIONS:
			self.language_combo.addItem(tr(key), code)
		current_lang_index = self.language_combo.findData(language_preference)
		if current_lang_index >= 0:
			self.language_combo.setCurrentIndex(current_lang_index)
		self.language_combo.currentIndexChanged.connect(self.language_changed)
		layout.addWidget(lang_label)
		layout.addWidget(self.language_combo)

		for label in button_states.keys():
			button = QPushButton(tr(label))
			button.clicked.connect(lambda checked, label=label: self.toggle_button(label))
			layout.addWidget(button)

		global_combo_audio_compass = QComboBox()
		global_combo_audio_compass.addItems([tr(k) for k in audio_compass_options])
		global_combo_audio_compass.setCurrentIndex(audio_compass_selection)
		global_combo_audio_compass.currentIndexChanged.connect(self.audio_compass_changed)
		layout.addWidget(global_combo_audio_compass)

		panel.setLayout(layout)
		self.tab_widget.addTab(panel, tr("ui.tab.audio_toggles"))

	def toggle_button(self, label):
		global button_states
		global configuration_values
		global audio_compass_selection
		if label == "toggle.benchmark" and button_states[label] == False:
			button_states[label] = not button_states[label]
			speak(tr("tts.benchmark_start"))
		elif label == "toggle.benchmark" and button_states[label] == True:
			button_states[label] = not button_states[label]
			speak(tr("tts.benchmark_canceled"))
		if label == "action.config.save":
			save_configuration(button_states, configuration_values, audio_compass_selection, language_preference)

		if label != "toggle.benchmark" and label != "action.config.save":
			button_states[label] = not button_states[label]
			speak(tr("tts.toggle_generic", label=tr(label), state=button_states[label]))

	def audio_compass_changed(self, index):
		global audio_compass_selection
		audio_compass_selection = index
		speak(tr("tts.compass_mode_changed", mode=tr(audio_compass_options[index])))

	def language_changed(self, index):
		global language_preference
		selected_lang = self.language_combo.itemData(index)
		if selected_lang not in SUPPORTED_LANGUAGES:
			return
		language_preference = selected_lang
		save_configuration(button_states, configuration_values, audio_compass_selection, language_preference)
		speak(tr("tts.restart_required"))

	def add_edit_panel(self):
		panel = QWidget()
		layout = QVBoxLayout()

		global value_variables
		for label_text in value_variables.keys():
			hbox = QVBoxLayout()
			lbl = QLabel(tr(label_text))
			edit = QLineEdit()
			edit.setAccessibleName(tr(label_text))
			edit.setValidator(QIntValidator(0, 10000))
			current_value = value_variables.get(label_text)
			if isinstance(current_value, int):
				edit.setText(str(current_value))
			hbox.addWidget(lbl)
			hbox.addWidget(edit)
			value_variables[label_text] = edit
			layout.addLayout(hbox)

		submit_button = QPushButton(tr("ui.button.submit"))
		submit_button.clicked.connect(self.submit_values)
		layout.addWidget(submit_button)

		panel.setLayout(layout)
		self.tab_widget.addTab(panel, tr("ui.tab.sensitivity"))

	def submit_values(self):
		global value_variables
		all_values_valid = True

		for label, edit in value_variables.items():
			text = edit.text().strip()
			if text and text.isdigit():
				value_variables[label] = int(text)
			elif text:
				all_values_valid = False

		if not all_values_valid:
			speak(tr("tts.invalid_integers"))
		else:
			speak(tr("tts.all_values_set"))
def mainStart():
	if __name__ == '__main__':
		app = QApplication([])
		main_window = MainWindow()
		main_window.show()
		app.exec_()
def updateVars():
	global configuration_values
	global speedInterval
	global speedSense
	global elevationSense
	global compassSense
	global maxTF
	global maxTR
	global bmSpeed
	global bmMonitor
	global metric
	global speakingTemp
	global speakingSusp
	global speakingGear
	global speakingCompass
	global speakingElevation
	global speakingSpeed
	global audioCompass
	global compassClicks
	global speedMon
	global elevationSensor
	global suspAudio
	global tempAudio
	global metricString
	global button_states
	global value_variables
	global audio_compass_selection
	if isinstance(value_variables["setting.speed.interval"], int):
		speedInterval=value_variables["setting.speed.interval"]
		configuration_values["setting.speed.interval"] = speedInterval
	if isinstance(value_variables["setting.speed.sensitivity"], int):
		speedSense=value_variables["setting.speed.sensitivity"]
		configuration_values["setting.speed.sensitivity"] = speedSense
	if isinstance(value_variables["setting.elevation.sensitivity"], int):
		elevationSense=value_variables["setting.elevation.sensitivity"]
		configuration_values["setting.elevation.sensitivity"] = elevationSense
	if isinstance(value_variables["setting.compass.sensitivity"], int):
		compassSense=value_variables["setting.compass.sensitivity"]
		configuration_values["setting.compass.sensitivity"] = compassSense
	if isinstance(value_variables["setting.tire_temp.front_max"], int):
		maxTF=value_variables["setting.tire_temp.front_max"]
		configuration_values["setting.tire_temp.front_max"] = maxTF
	if isinstance(value_variables["setting.tire_temp.rear_max"], int):
		maxTR=value_variables["setting.tire_temp.rear_max"]
		configuration_values["setting.tire_temp.rear_max"] = maxTR
	if isinstance(value_variables["setting.benchmark.target_speed"], int):
		bmSpeed=value_variables["setting.benchmark.target_speed"]
		configuration_values["setting.benchmark.target_speed"] = bmSpeed
	metric=button_states["toggle.measurement.metric"]
	metricString = "KMH" if metric else "MPH"
	speakingTemp=button_states["toggle.sr.tire_temps"]
	speakingSusp=button_states["toggle.sr.suspension"]
	speakingGear=button_states["toggle.sr.gears"]
	speakingCompass=button_states["toggle.sr.compass"]
	speakingElevation=button_states["toggle.sr.elevation"]
	speakingSpeed=button_states["toggle.sr.speed"]
	if audio_compass_selection == 0:
		audioCompass = False
		compassClicks=False
	elif audio_compass_selection == 1:
		audioCompass=True
		compassClicks=False
	elif audio_compass_selection == 2:
		audioCompass=False
		compassClicks=True
	elif audio_compass_selection == 3:
		audioCompass=True
		compassClicks=True
	speedMon = button_states["toggle.audio.speed"]
	elevationSensor=button_states["toggle.audio.elevation"]
	suspAudio= button_states["toggle.audio.suspension"]
	tempAudio=button_states["toggle.audio.tire_temp"]
	bmMonitor = button_states["toggle.benchmark"]
	if bmMonitor == False:
		armedBenchmark=False
		startBenchmark=False
		bmStartTime= 0
		bmEndTime = 0




#Wrapping the speech output to be more user friendly by defaulting the interrupt to on.
def speak(text,interrupt=True):
	o.output(text, interrupt)
def print_Speak(speaking, message):
	if speaking == True:
		speak(message)
		print(message)
	else:
		print(message)

def execute_After(func, interval):
	"""
	Executes a function after a given interval if not executed in that interval.
	:param func: Function to be executed.
	:param interval: Time in seconds after which the function will be executed.
	"""
	current_time = time.time()
	if func not in last_executed or current_time - last_executed[func] >= interval:
		last_executed[func] = current_time
		timer = threading.Timer(interval, func)
		timer.start()

# Function to load sound file
def load_sound(file_path):
	return AudioSegment.from_file(file_path)

# Function 2: Adjust stereo panning
def set_stereo_panning(sound, panning):
	return sound.pan(panning)

# Function 3: Adjust pitch
def set_pitch(sound, pitch):
	new_sample_rate = int(sound.frame_rate * (2 ** pitch))
	return sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})

# Function 4: Adjust volume
def set_volume(sound, volume):
	return sound + volume
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
newClick=click
newCompass= sound
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
	# Convert the heading to a panning value (-1 to 1)
	# 270 degrees -> -1, 90 degrees -> 1
	panning = (heading - 180) / 90
	if panning > 1:
		panning = -2 + panning
	elif panning < -1:
		panning = 2 + panning

	# Correct the panning logic
	if 270 > heading > 90:
		panning = -panning

	# Adjust panning
	sound = sound.pan(panning)
	# Adjust pitch 
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
	sound = set_pitch(sound, pitch)
	return sound


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
	# Wait for the event to be set
		sound_events[sound_name].wait()
		# Play sound
		threadSound.play()
		# Logic to stop the sound when the event is cleared
		sound_events[sound_name].clear()

def create_sound_thread(sound_name, soundHandle):
	if isinstance(soundHandle, list):
		# Handle a list of sounds
		for index, single_sound in enumerate(soundHandle):
			sound_events[f"{sound_name}_{index}"] = threading.Event()
			thread = threading.Thread(target=sound_thread_function, args=(f"{sound_name}_{index}", soundHandle, index))
			thread.daemon = True
			thread.start()
	else:
		# Handle a single sound
		sound_events[sound_name] = threading.Event()
		thread = threading.Thread(target=sound_thread_function, args=(sound_name, soundHandle))
		thread.daemon = True
		thread.start()

def addSound(sound_name, index=None):
	if index is not None:
		sound_events[f"{sound_name}_{index}"].set()
	else:
		sound_events[sound_name].set()

# Example usage for compassSounds list
#create_sound_thread("compass", compassSounds)
# To play a specific sound from compassSounds
#addSound("compass", index=45)  # Plays the sound at index 45 in compassSounds
def convertDir(degrees):
	if 337.5 <= degrees < 360 or 0 <= degrees < 22.5:
		return tr("dir.north")
	elif 22.5 <= degrees < 67.5:
		return tr("dir.northeast")
	elif 67.5 <= degrees < 112.5:
		return tr("dir.east")
	elif 112.5 <= degrees < 157.5:
		return tr("dir.southeast")
	elif 157.5 <= degrees < 202.5:
		return tr("dir.south")
	elif 202.5 <= degrees < 247.5:
		return tr("dir.southwest")
	elif 247.5 <= degrees < 292.5:
		return tr("dir.west")
	elif 292.5 <= degrees < 337.5:
		return tr("dir.northwest")
	else:
		return tr("dir.invalid")
def speedConvert(speed_mps):
	if metric == False:
		return speed_mps * 2.23694
	if metric == True:
		return speed_mps * 3.6
def speedBenchMark(curRPM, idleRPM, curSpeed, curTime):
	global button_states
	global bmMonitor
	global armedBenchmark
	global bmStartTime
	global bmEndTime
	global bmTotalTime
	global startBenchmark
	global bmSpeed
	speed=curSpeed
	curRPM = round(curRPM)
	idleRPM = round(idleRPM)
	if bmMonitor == True:
		speed=speedConvert(speed)
		if armedBenchmark == False and round(curRPM) == round(idleRPM) and round(speed) == 0:
			armedBenchmark = True
			print("benchmark ready")
		if armedBenchmark == True and curRPM != idleRPM and startBenchmark == False:
			startBenchmark = True
			bmStartTime = curTime
			print("Timer started.")
		if armedBenchmark == True and startBenchmark == True and speed >= bmSpeed:
			bmMonitor = False
			button_states["toggle.benchmark"] = False
			armedBenchmark = False
			startBenchmark = False
			bmEndTime=curTime
			bmTotalTime = (bmEndTime-bmStartTime)/1000
			print_Speak(True,tr("tts.benchmark_completed", speed=bmSpeed, unit=metricString, time=bmTotalTime))
# Set the server's port
port = 5300

# Create a socket object for UDP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('', port))
server_socket.settimeout(1)
print(f"Listening for packets on port {port}")

def packetReceiver():
	global packed_data
	global packeting
	# Continuously listen for packets
	while packeting:
		# Receive packets
		try:
			data, addr = server_socket.recvfrom(332)  # Adjust buffer size if necessary
			# Define the format string for unpacking
			format_string = 'iI27f4i20f5i17fH6B4bfi'
			# Check if the received data matches the expected size
			if len(data) >= 0:
				# Pack the data according to the specified format
				packed_data = struct.unpack(format_string, data[:struct.calcsize(format_string)])
			else:
				print("Received data is shorter than expected format at "+str(len(data))+".")
		except socket.timeout:
			continue  # This allows checking the packeting flag periodically
		except Exception as e:
			print(f"Error: {e}")
			break  # Handle other exceptions, e.g., socket being closed
		speedBenchMark(packed_data[4], packed_data[3], packed_data[61], packed_data[1])

def processPacket():
	unpacked_data = []
	unpacked_data = packed_data
	# Print the unpacked data (or process/store it as needed)
	global speedInterval
	global curSpeedInt
	global preSpeed
	global preGear
	global bottomedFL
	global bottomedFR
	global bottomedRL
	global bottomedRR
	global maxTF
	global maxTR
	global frontMax
	global rearMax
	global preTTFl
	global preTTFR 
	global preTTRL 
	global preTTRR
	global preSuspFL
	global preSuspFR 
	global preSuspRL
	global preSuspRR
	global preYaw
	global prePitch
	global preRoll
	global preDir
	global preClick
	global speedMonitor
	global exceed
	global preElevation
	global elevationSense
	global compassSense
	curPitch = round(unpacked_data[15]*100)
	curRoll = round(unpacked_data[16]*100)
	if prePitch != curPitch:
		prePitch = curPitch
#		print_Speak(False, str(curPitch))
	if curRoll != preRoll:
#		print_Speak(True, str(curRoll))
		preRoll = curRoll
	curGear = unpacked_data[81]
	if curGear != preGear and curGear != 11 and curGear != 0:
		print_Speak(speakingGear, tr("tts.gear", gear=curGear))
		preGear=curGear
	elif curGear != preGear and curGear == 0:
		print_Speak(speakingGear, tr("tts.reverse"))
		preGear=curGear
	TTFL = unpacked_data[64]
	TTFR = unpacked_data[65]
	TTRL = unpacked_data[66]
	TTRR = unpacked_data[67]
	if TTFL >= maxTF and frontMax == False or TTFR >= maxTF and frontMax == False:
		print_Speak(speakingTemp, tr("tts.tire_front_exceeded", limit=maxTF, left=TTFL, right=TTFR))
		frontMax = True
		if tempAudio == True:
			addSound('front temp')
	if TTRL >= maxTR and rearMax == False or TTRR >= maxTR and rearMax == False:
		print_Speak(speakingTemp, tr("tts.tire_rear_exceeded", limit=maxTR))
		rearMax = True
		if tempAudio == True:
			addSound('rear temp')
	if TTFL < maxTF and TTFR < maxTF and frontMax == True:
		print_Speak(speakingTemp, tr("tts.tire_front_below", limit=maxTF, left=TTFL, right=TTFR))
		frontMax=False
	if TTRL < maxTR and TTRR < maxTR and rearMax == True:
		print_Speak(speakingTemp, tr("tts.tire_rear_below", limit=maxTR))
		rearMax = False
	suspFL = unpacked_data[17]
	suspFR = unpacked_data[18]
	suspRL = unpacked_data[19]
	suspRR = unpacked_data[20]
	if suspFL >= 1 and bottomedFL == False:
		print_Speak(speakingSusp, tr("tts.susp.fl"))
		bottomedFL = True
		if suspAudio == True:
			addSound('Suspfl')
	if suspFL < 1 and bottomedFL == True:
		bottomedFL = False
	if suspFR >= 1 and bottomedFR == False:
		print_Speak(speakingSusp, tr("tts.susp.fr"))
		bottomedFR = True
		if suspAudio == True:
			addSound('Suspfr')
	if suspFR < 1 and bottomedFR == True:
		bottomedFR = False
	if suspRL >= 1 and bottomedRL == False:
		print_Speak(speakingSusp, tr("tts.susp.rl"))
		bottomedRL = True
		if suspAudio == True:
			addSound('Susprl')
	if suspRL < 1 and bottomedRL == True:
		bottomedRL = False
	if suspRR >= 1 and bottomedRR == False:
		print_Speak(speakingSusp, tr("tts.susp.rr"))
		bottomedRR = True
		if suspAudio == True:
			addSound('Susprr')
	if suspRR < 1 and bottomedRR == True:
		bottomedRR = False
	if preElevation < unpacked_data[59] or preElevation > unpacked_data[59]:
		curElevation = unpacked_data[59]
		if abs(preElevation-curElevation) >= elevationSense:
			if curElevation > preElevation:
				if elevationSensor == True:
					addSound('ascend')
				print_Speak(speakingElevation, tr("tts.ascending"))
			if curElevation < preElevation:
				if elevationSensor == True:
					addSound('descend')
				print_Speak(speakingElevation, tr("tts.descending"))
			preElevation=curElevation
	curYaw = int((unpacked_data[14] * (180 / math.pi)) + 180)
	if curYaw == 360:
		curYaw = 0
	yawDiff = int(abs(preYaw - curYaw) % 360)
	clickDiff = int(abs(preClick - curYaw) % 360)
	if clickDiff > 180:
		clickDiff = 360 - clickDiff
	if yawDiff > 180:
		yawDiff = 360 - yawDiff
	if preYaw != curYaw and yawDiff > 1:
		preYaw=curYaw
		if abs(clickDiff) >= compassSense and compassClicks == True:
			preClick=curYaw
			addSound('click', preYaw)
		curDir = convertDir(round(curYaw))
		if(preDir!=curDir):
			preDir = curDir
			if audioCompass == True:
				addSound('compass', preYaw)
			print_Speak(speakingCompass, curDir)
	curSpeed = speedConvert(unpacked_data[61])
	if curSpeed != preSpeed and abs(curSpeed-preSpeed) >= speedSense:
		preSpeed=curSpeed
		if curSpeed > preSpeed:
			curSpeedInt = curSpeedInt+1
			if speedMon == True:
				addSound('speed')
		else:
			curSpeedInt = curSpeedInt-1
			if speedMon == True:
				addSound('speed')
		if speedInterval == 0 or curSpeedInt % speedInterval == 0:
			print_Speak(speakingSpeed, tr("tts.speed_value", speed=int(curSpeed), unit=metricString))

def shutDown():
	print("Stopping the server...")
	pygame.mixer.quit()
	packeting=False
	time.sleep(2)
	server_socket.close()
	packetThread.join()




mainThread = threading.Thread(target=mainStart)
packetThread = threading.Thread(target=packetReceiver)
button_states, value_variables, audio_compass_selection, language_preference = load_configuration()
language_preference = language_preference if language_preference in SUPPORTED_LANGUAGES else detect_system_language()
load_translations(language_preference)
configuration_values = value_variables.copy()
speedInterval = configuration_values.get("setting.speed.interval", speedInterval)
speedSense = configuration_values.get("setting.speed.sensitivity", speedSense)
elevationSense = configuration_values.get("setting.elevation.sensitivity", elevationSense)
compassSense = configuration_values.get("setting.compass.sensitivity", compassSense)
maxTF = configuration_values.get("setting.tire_temp.front_max", maxTF)
maxTR = configuration_values.get("setting.tire_temp.rear_max", maxTR)
bmSpeed = configuration_values.get("setting.benchmark.target_speed", bmSpeed)
metric = button_states.get("toggle.measurement.metric", metric)
metricString = "KMH" if metric else "MPH"
try:
	packetThread.start()
	mainThread.start()
	create_sound_thread('descend', descend)
	create_sound_thread('ascend', ascend)
	create_sound_thread('front temp', temp)
	create_sound_thread('rear temp', tempR)
	create_sound_thread('Suspfl', Suspfl)
	create_sound_thread('Suspfr', Suspfr)
	create_sound_thread('Susprl', Susprl)
	create_sound_thread('Susprr', Susprr)
	create_sound_thread('speed', speed)
	create_sound_thread('click', clickSounds)
	create_sound_thread('compass', compassSounds)

	while True:
		updateVars()
		if packed_data != []:
			processPacket()
		time.sleep(.05)
		if mainThread.is_alive() == False:
			shutDown()
			break
except KeyboardInterrupt:
	# Close the socket when interrupted (e.g., by Ctrl+C)
	shutDown()