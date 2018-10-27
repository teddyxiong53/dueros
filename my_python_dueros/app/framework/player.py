import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst

Gst.init(None)

class Player(object):
	def __init__(self):
		self.player = Gst.ElementFactory.make("playbin", "player")
		self.bus = self.player.get_bus()
		self.bus.add_signal_watch()
		self.bus.enable_sync_message_emission()
		
	def play(self, uri):
		self.player.set_state(Gst.State.NULL)
		self.player.set_property("uri", uri)
		self.player.set_state(Gst.State.PLAYING)
		
	def stop(self):
		self.player.set_state(Gst.State.NULL)
		
	def pause(self):
		self.player.set_state(Gst.State.PAUSED)
		
	def resume(self):
		self.player.set_state(Gst.State.PLAYING)
		
	def add_callback(self, name, callback):
		if not callable(callback):
			return 
			
		def on_message(bus, message):
			callback()
			
		self.bus.connect('sync-message::{}'.format(name), on_message)
		
		
	@property
	def duration(self):
		success, duration = self.player.query_duration(Gst.Format.TIME)
		if success:
			return int(duration/Gst.MSECOND)
			
	@property
	def position(self):
		success, position = self.player.query_position(Gst.Format.TIME)
		if not success:
			position = 0
		return int(position/Gst.MSECOND)
		
	@property
	def state(self):
		_, state, _ = self.player.get_state(Gst.SECOND)
		if state != Gst.State.PLAYING:
			return "FINISHED"
		else:
			return "PLAYING"
		