import os, datetime, dateutil.parser
from threading import Timer
import uuid


class Alerts(object):
	STATES = {"IDLE", "FOREGROUND", "BACKGROUND"}
	def __init__(self, dueros, player):
		self.namespace = "ai.dueros.device_interface.alerts"
		self.dueros = dueros
		self.player = player 
		self.player.add_callback("eos", self.stop)
		self.player.add_callback("error", self.stop)
		
		alarm = os.path.realpath(os.path.join(os.path.dirname(__name__), "../resources/alarm.wav"))
		self.alarm_uri = "file://{}".format(alarm)
		self.all_alerts = {}
		self.active_alerts = {}
		
	def stop(self):
		for token in self.active_alerts.keys():
			self.__alert_stopped(token)
		self.active_alerts = {}
		
	def set_alert(self, directive):
		payload = directive['payload']
		token = payload['token']
		scheduled_time = dateutil.parser.parse(payload['scheduledTime'])
		
		if token in self.all_alerts:
			pass
			
		self.all_alerts[token] = payload
		interval = scheduled_time - dateutil.datetime.now(scheduled_time.tzinfo)
		self.__set_alert_succeeded(token)
		
	def delete_alert(self, directive):
		token = directive['payload']['token']
		if token in self.active_alerts:
			self.__alert_stopped(token)
			
		if token in self.all_alerts:
			del self.all_alerts[token]
			
		self.__delete_alert_succeeded(token)
		
	def __start_alert(self, token):
		pass
		
		