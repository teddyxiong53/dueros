import os, tempfile, uuid

class AudioPlayer(object):
	STATES = {'IDLE', 'PLAYING', 'STOPPED', 'PAUSED', 'BUFFER_UNDERRUN', 'FINISHED'}
	
	def __init__(self, dueros, player):
		self.namespace = "ai.dueros.device_interface.audio_player"
		self.dueros = dueros
		self.token = ''
		self.state = 'IDLE'
		
		self.player = player
		self.player.add_callback('eos', self.__playback_finished)
		self.player.add_callback('error', self.__playback_finished)
		
	"""
	message sample:
	{
		"directive": {
			"namespace": "AudioPlayer",
			"name": "Play",
			"messageId": "xxx",
			"dialogRequestId": "xxx"
		},
		"payload": {
			"playBehavior": "xxx",
			"audioItem" : {
				"audiItemId": "xxx",
				"stream": {
					"url": "xxx",
					"streafFormat": "AUDIO_MPEG",
					"offsetInMilliseconds": xxx, # long type
					"expiryTime": "xxx",
					"progressReport": {
						"progressReportDelayInMilliseconds": xxx,
						"progressReportIntervalInMilliseconds": xxx
					},
					"token": "xxx",
					"expectedPreviousToken": "xxx"
				}
			}
		}
	}
	"""
	
	def pause(self):
		self.player.pause()
		self.__playback_paused()
		
	def resume(self);
		self.player.resume()
		self.__playback_resumed()
		
	def play(self, directive):
		behavior = directive['payload']['playBehavior']
		self.token = directive['payload']['audioItem']['stream']['token']
		audio_url = directive['payload']['audioItem']['stream']['url']
		if audio_url.startswith("cid:"):
			mp3_file = os.path.join(tempfile.gettempdir(), audio_url[:4] + ".mp3")
			if os.path.isfile(mp3_file):
				self.player.play("file://{}".format(mp3_file))
				self.__playback_started()
		else:
			self.player.play(audio_url)
			self.__playback_started()
			
	def stop(self, directive):
		self.player.stop()
		self.__playback_stopped()
		
	def clear_queue(self, directive):
		self.__playback_queue_cleared()
		behavior = directive['payload']['clearBehavior']
		if behavior == 'CLEAR_ALL':
			self.player.stop()
		elif behavior == 'CLEAR_ENQUEUED':
			pass
			
	def __playback_started(self):
		self.state = 'PLAYING'
		event = {
			"header": {
				"namespace": self.namespace,
				"name": "PlaybackStarted",
				"messageId": uuid.uuid4().hex
			},
			"payload": {
				"token": self.token,
				"offsetInMilliseconds": self.player.position
			}
		}
		self.dueros.send_event(event)
		
		
	def __playback_stopped(self):
		self.state = 'STOPPED'
		event = {
			"header": {
				"namespace": self.namespace,
				"name": "PlaybackStopped",
				"messageId": uuid.uuid4().hex
			},
			"payload": {
				"token": self.token,
				"offsetInMilliseconds": self.player.position
			}
		}
		self.dueros.send_event(event)
		
	def __playback_nearly_finished(self):
		event = {
			"header": {
				"namespace": self.namespace,
				"name": "PlaybackNearlyFinished",
				"messageId": uuid.uuid4().hex
			},
			"payload": {
				"token": self.token,
				"offsetInMilliseconds": self.player.position
			}
		}
		self.dueros.send_event(event)
		
	def __playback_finished(self):
		self.state = "FINISHED"
		event = {
			"header": {
				"namespace": self.namespace,
				"name": "PlaybackFinished",
				"messageId": uuid.uuid4().hex
			},
			"payload" : {
				"token": self.token,
				"offsetInMilliseconds": self.player.position
			}
		}
		self.dueros.send_event(event)
		
	def __playback_failed(self):
		self.state = "STOPPED"
		
	def __playback_stopped(self):
		self.state = "STOPPED"
		event = {
			"header": {
				"namespace": self.namespace,
				"name": "PlaybackStopped",
				"messageId": uuid.uuid4().hex
			},
			"payload": {
				"token": self.token,
				"offsetInMilliseconds": self.player.position
			}
		}
		self.dueros.send_event(event)
		
	def __playback_paused(self):
		self.state = "PAUSED"
		event = {
			"header" : {
				"namespace": self.namespace,
				"name": "PlaybackPaused",
				"messageId": uuid.uuid4().hex
			},
			"payload": {
				"token": self.token,
				"offsetInMilliseconds": self.player.positon
			}
		}
		self.dueros.send_event(event)
		
	def __playback_resumed(self):
		self.state = "PLAYING"
		event = {
			"header": {
				"namespace": self.namespace,
				"name": "PlaybackResumed",
				"messageId": uuid.uuid4().hex
			},
			"payload": {
				"token": self.token,
				"offsetInMilliseconds": self.player.position
			}
		}
		self.dueros.send_event(event)
		
	@property
	def context(self):
		if self.state != "PLAYING":
			offset = 0
		else:
			offset = self.player.position
		return {
			"header": {
				"namespace": self.namespace,
				"name": "PlaybackState"
			},
			"payload": {
				"token": self.token,
				"offsetInMilliseconds": offset,
				"playerActivity": self.state
			}
		}