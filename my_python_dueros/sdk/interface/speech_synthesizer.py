import os, tempfile, threading, uuid

"""
sample message
{
	"directive": {
		"header": {
			"namespace": "SpeechSynthesizer",
			"name": "Speak",
			"messageId": "xxx",
			"dialogRequestId": "xxx"
		},
		"payload": {
			"url": "xxx",
			"format": "AUDIO_MPEG",
			"token": "xxx"
		}
	}
}
Content-Type: application/octet-stream
Content-ID: {{Audio Item CID}}
{{0000111100000}}
"""
class SpeechSynthesizer(object):
	STATES = {"PLAYING", "FINISHED"}
	
	def __init__(self, dueros, player):
		self.namespace = "ai.dueros.device_interface.voice_output"
		self.dueros = dueros
		self.player = player
		self.token = ""
		self.state = "FINISHED"
		self.finished = threading.Event()
		
		self.player.add_callback("eos", self.__speech_finished)
		self.player.add_callback("error", self.__speech_finished)
		
		
	def stop(self):
		self.finished.set()
		self.player.stop()
		self.state = "FINISHED"
		
	def speak(self, directive):
		if "dialogRequestId" in directive['header']:
			dialog_request_id = directive['header']['dialogRequestId']
			if self.dueros.speech_recognizer.dialog_request_id != dialog_request_id:
				return 
		self.token = directive['payload']['token']
		url = directive['payload']['url']
		if url.startswith['cid:']:
			mp3_file = os.path.join(tempfile.gettempdir(), url[4:]+".mp3)
			if os.path.isfile(mp3_file):
				self.finished.clear()
				self.player.play("file://{}".format(mp3_file))
				self.__speech_started()
				
				self.dueros.state_listener.on_speaking()
				self.finished.wait()
				os.system("rm -rf {}".format(mp3_file))
				
	def __speech_started(self):
		self.state = 'PLAYING'
		event = {
			"header": {
				"namespace": self.namespace,
				"name": "SpeechStarted",
				"messageId": uuid.uuid4().hex
			},
			"payload": {
				"token": self.token
			}
		}
		self.dueros.send_event(event)
		
	def __speech_finished(self):
		self.dueros.state_listener.on_finished()
		
		self.finished.set()
		
		self.state = "FINISHED"
		event = {
			"header": {
				"namespace": self.namespace,
				"name": "SpeechFinished",
				"messageId": uuid.uuid4().hex
			},
			"payload": {
				"token": self.token
			}
		}
		self.dueros.send_event(event)
		
	@property
	def context(self):
		offset = self.player.position if self.state == "PLAYING" else 0
		return {
			"header": {
				"namespace": self.namespace,
				"name": "SpeechState"
			},
			"payload" : {
				"token": self.token,
				"offsetInMilliseconds": offset,
				"playerActivity": self.state
			}
			
		}
		