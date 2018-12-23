import logging
import uuid
import os, sys
import tempfile
import requests

import cgi

try:
	import Queu as queue
except ImportError:
	import queue
	
import threading
import datetime

import hyper
import sdk.configurate

import sdk.sdk_config as sdk_config

from sdk.interface.alerts import Alerts
from sdk.interface.audio_player import AudioPlayer
from sdk.interface.speaker import Speaker
from sdk.interface.speech_recognizer import SpeechRecognizer
from sdk.interface.speech_synthesizer import SpeechSynthesizer
from sdk.interface.system import System



logging.basicConfig(level=sdk_config.LOGGER_LEVEL)
logger = logging.getLogger(__name__)



class DuerOSStateListener(object):
	def __init__(self):
		pass
		
	def on_listening(self):
		logger.info("[dueros] listening")
		
	def on_thinking(self):
		logger.info("[dueros] thinking")
		
	def on_speaking(self):
		logger.info("[dueros] speaking")
		
	def on_finished(self):
		logger.info("[dueros] finished")
		
class DuerOS(object):
	
	def __init__(self, player):
		self.event_queue = queue.Queue()
		self.speech_recognizer = SpeechRecognizer(self)
		self.speech_synthesizer = SpeechSynthesizer(self, player)
		self.audio_player = AudioPlayer(self, player)
		self.speaker = Speaker(self)
		self.alerts = Alerts(self, player)
		self.system = System(self)
		
		self.state_listener = DuerOSStateListener()
		
		self.put = self.speech_recognizer.put
		
		self.done = False
		self.requests = requests.Session()
		
		self.__config = sdk.configurate.load()
		
		self.__config['host_url'] = "dueros-h2.baidu.com"
		self.__config['api'] = "dcs/v1"
		self.__config['refresh_url'] = "https://openapi.baidu.com/oauth/2.0/token"
		self.last_activity = datetime.datetime.utcnow()
		self.__ping_time = None
		self.directive_listener = None
		
	def set_directive_listener(self, listener):
		if callable(listener):
			self.directive_listener = listener
		else:
			raise ValueError("directive listener is not callable")
	def start(self):
		self.done = False
		t = threading.Thread(target=self.run)
		t.daemon = True
		t.start()
		
	def stop(self):
		self.done = True
		
	def listen(self):
		self.speech_recognizer.recognize()
		
	def send_event(self, event, listener =None, attachment=None):
		self.event_queue.put((event, listener, attachment))
		
	def run(self):
		while not self.done:
			try:
				self.__run()
			except AttributeError as e:
				logger.exception(e)
				continue
			except hyper.http20.exceptions.StreamResetError as e:
				logger.exception(e)
				continue
			except ValueError as e:
				logging.exception(e)
				sys.exit(1)
			except Exception as e:
				logger.exception(e)
				continue
				
				
	def __run(self):
		conn = hyper.HTTP20Connection('{}:443'.format(self.__config['host_url']), force_proto='h2')
		headers = {
			"authorization": "Bearer {}".format(self.token)
		}
		if 'dueros-device-id' in self.__config:
			headers['dueros-device-id'] = self.__config['dueros-device-id']
		downchannel_id = conn.request('GET', '/{}/directives'.format(self.__config['api']), headers=headers)
		downchannel_response = conn.get_response(downchannel_id)
		
		if downchannel_response.status != 200:
			raise ValueError("/directives requests return {}".format(downchannel_response.status))
		ctype, pdict = cgi.parse_header(downchannel_response.headers['content-type'][0].decode('utf-8'))
		downchannel_boundary = '--{}'.format(pdict['boundary']).encode('utf-8')
		downchannel = conn.streams[downchannel_id]
		downchannel_buffer = io.ByteIO()
		eventchannel_boundary = 'baidu-voice-engine'
		
		self.__ping_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=240)
		self.event_queue.queue.clear()
		self.system.synchronize_state()
		
		while not self.done:
			try:
				event,listener, attachment = self.event.get(timeout=0.25)
			except queue.Empty:
				event = None
			while conn._sock.can_read:
				conn._single_read()
				
			while downchannel.data:
				framebytes = downchannel._read_one_frame()
				self.__read_response(framebytes, downchannel_boundary, downchannel_buffer)
				
			if event is None:
				self.__ping(conn)
				continue
				
			headers = {
				':method': 'POST',
				':scheme': 'https',
				':path': '/{}/events'.format(self.__config['api']),
				'authorization': 'Bearer {}'.format(self.token),
				'content-type': 'multipart/form-data; boundary={}'.format(downchannel_boundary)
				
			}
			if 'dueros-device-id' in self.__config:
				headers['dueros-device-id'] = self.__config['dueros-device-id']
			
			stream_id = conn.putrequest(headers[':method'], headers[':path'])
			default_headers = (':method', ':scheme', ':authority', ':path')
			
	def __read_response(self, response, boundary=None, buffer=None):
		if boundary:
			endboundary = boundary + b"--"
		else:
			ctype,pdict = cgi.parse_header(
				response.headers['content-type'][0].decode('utf-8')
			)
			boundary = "--{}".format(pdict['boundary'].encode('utf-8')
			endboundary = "--{}--".format(pdict['boundary']).encode('utf-8')
			
		on_boundary = False
		in_header = False
		in_payload = False
		first_payload_block = False
		content_type = None
		content_id = None
		
		def iter_lines(response, delimiter=None):
			pending = None
			for chunk in reponse.read_chunked():
				if pending is not None:
					chunk = pending + chunk
				if delimiter:
					lines = chunk.split(delimiter)
				else:
					lines = chunk.splitlines()
					
				if lines and lines[-1] and chunk and chunk[-1][-1] == chunk[-1]:
					pending = lines.pop()
				else:
					pending = None
				for line in lines:
					yield line
					
			if pending is not None:
				yield pending
				
		directives = []
		if isinstance(response, bytes):
			buffer.seek(0)
			lines = (buffer.read() + response).split(b'\r\n')
			buffer.flush()
		else:
			lines = iter_lines(response, delimiter=b'\r\n')
			
		for line in lines:
			if line == boundary or line == endboundary:
				on_boundary = True
				if in_payload:
					in_payload = False
					if content_type == "application/json":
						logger.info("Finished download json")
						utf8_payload = json.loads()
						
						
	def __handle_directive(self, directive):
		if 'directive_listener' in dir(self):
			self.directive_listener(directive)
			
		try:
			namespace = directive['header']['namespace']
			namespace = self.__namespace_convert(namespace)
			if not namespace :
				return
			name = directive['header']['name']
			name = self.__name_convert(name):
			if hasattr(self, namespace):
				interface = getattr(self, namespace)
				directive_func = getattr(interface, name, None)
				if directive_func:
					directive_func(directive)
				else:
					logger.info('{}.{} is not implemented'.format(namespace, name))
			else:
				logger.info("{} is not implement".format(namespace))
		except KeyError as e:
			logger.exception(e)
		except Exception as e:
			logger.exception(e)
			
			
	def __ping(self, connection):
		if datetime.datetime.utcnow() >= self.__ping_time:
			connection.ping(uuid.uuid4().hex[:8])
			logger.debug('ping at {}'.format(datetime.datetime.utcnow().strftime("%a %b %d %H:%M%S %Y")))
			self.__ping_time = datetime.datetime.utcno() + datetime.timedelta(seconds=240)
			
	def __namespace_convert(self, namespace):
		if namespace == 'ai.dueros.device_interface.voice_output':
			return 'speech_synthesizer'
		elif namespace == 'ai.dueros.device_interface.voice_input':
			return 'speech_recognizer'
		elif namespace == 'ai.dueros.device_interface.alerts':
			return 'alerts'
		elif namespace == 'ai.dueros.device_interface.audio_player':
			return 'audio_player'
		elif namespace == 'ai.dueros.device_interface.speaker_controller':
			return 'speaker'
		elif namespace == 'ai.dueros.device_interface.system':
			return 'system'
		else:
			return None
			
	def __name_convert(self, name):
		if name == 'StopListen':
			return 'stop_listen'
		elif name == 'Listen':
			return 'listen'
		elif name == 'Speak':
			return 'speak'
		elif name == 'SetVolume':
			return 'set_volume'
		elif name == 'AdjustVolume':
			return 'adjust_volume'
		elif name == 'SetMute':
			return 'set_mute'
		elif name == 'Play':
			return 'play'
		elif name == 'Stop':
			return 'stop'
		elif name == 'ClearQueue':
			return 'clear_queue'
		elif name == 'SetAlert':
			return 'set_alert'
		elif name == 'DeleteAlert':
			return 'delete_alert'
		elif name == 'HtmlView':
			return 'html_view'
		elif name == 'ResetUserInactivity':
			return 'reset_user_inactivity'
		elif name == 'SetEndpoint':
			return 'set_end_point'
		elif name == 'ThrowException':
			return 'throw_exception'
			