import logging, uuid
try:
	import Queue as queue
except ImportError:
	import queue
	
import sdk.sdk_config as sdk_config

logging.basicConfig(level=sdk_config.LOGGER_LEVEL)
logger = logging.getLogger("SpeechRecognizer")

class SpeechRecognizer(object):
	STATES = {"IDLE", "RECOGNIZING", "BUSY", "EXPECTING_SPEECH"}
	PROFILES = {"CLOSE_TALK", "NEAR_FIELD", "FAR_FIELD"}
	PRESS_AND_HOLD = {'type': "PRESS_AND_HOLD", "payload": {}}
	TAP = {"type": "TAP", "payload": {}}
	
	def __init__(self, dueros):
		self.namespace = "ai.dueros.device_interface.voice_input"
		self.dueros = dueros
		self.profile = "NEAR_FIELD"
		
		self.dialog_request_id = ""
		self.listening = False
		self.audio_queue = queue.Queue()
		
	def put(self, audio):
		if self.listening:
			self.audio_queue.put(audio)
			
	def recognize(self, dialog=None, timeout=10000):
		if self.listening:
			return
		self.audio_queue.queue.clear()
		self.listening = True
		self.dueros.state_listener.on_listening()
		
		def on_finished():
			self.dueros.state_listener.on_finished()
			if self.dueros.audio_player.state == "PAUSED":
				self.dueros.audio_player.resume()
				
		if self.dueros.speech_synthesizer.state == "PLAYING":
			self.dueros.speech_synthesizer.stop()
		elif self.dueros.audio_player.state == "PLAYING":
			self.dueros.audio_player.pause()
			
		self.dialog_request_id = dialog if dialog else uuid.uuid4().hex
		
		event = {
			"header": {
				"namespace": self.namespace,
				"name": "ListenStarted",
				"messageId": uuid.uuid4().hex
			},
			"payload": {
				"profile": self.profile,
				"format": "AUDIO_L16_RATE_16000_CHANNELS_1"
			}
		}
		
		def gen():
			time_elapsed = 0
			while self.listening or time_elapsed > timeout:
				try:
					chunk = self.audio_queue.get(timeout=1.0)
				except queue.Empty:
					break
				yield chunk
				time_elapsed += 10 # 10ms
				
			self.listening = false
			self.dueros.state_listener.on_thinking()
			
		self.dueros.send_event(event, listener=on_finished, attachment=gen())
		
	def stop_listen(self, directive):
		self.listening = False
		logger.info("StopCapture")
		
		
	def listen(self, directive):
		dialog = directive['header']['dialogRequestId']
		timeout = directive['payload']['timeoutInMilliseconds']
		self.recognize(dialog=dialog, timeout=timeout)
		
	def expect_speech_timeout(self):
		event = {
			"header": {
				"namespace": "self.namespace,
				"name": "ExpectSpeechTimeOut",
				"messageId": uuid.uuid4().hex
			},
			"payload" : {
			}
		}
		self.dueros.send_event(event)
		
	@property
	def context(self):
		return {
			"header": {
				"namespace": self.namespace,
				"name": "ListenStarted"
			},
			"payload": {
				"wakeword": "xiaoduxiaodu"
			}
		}