import os

from app.framework.player import Player

Class PromptTone(object):
	def __init__(self):
		self.player = Player()
		resource = os.path.realpath(os.path.join(os.path.dirname(__file__), "../resources/du.mp3"))
		self.resource_uri = "file://{}".format(resource)
		
	def play(self):
		self.player.play(self.resource_uri)
		
		