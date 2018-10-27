import logging
import sdk.sdk_config as sdk_config

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
	pass
	
