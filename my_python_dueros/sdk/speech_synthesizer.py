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
		url = directive[]