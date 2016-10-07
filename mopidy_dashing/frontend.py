from __future__ import unicode_literals

import pykka
import urllib2
import logging
import json

import requests

from mopidy import core
from mopidy.models import ModelJSONEncoder

logger = logging.getLogger(__name__)

class DashingFrontend(pykka.ThreadingActor, core.CoreListener):
	def __init__(self, config, core):
		super(DashingFrontend, self).__init__()
		self.config = config	
		self.core = core

		self.url = "http://%s:%s%s" % (
			config['dashing']['hostname'], 
			config['dashing']['port'], 
			config['dashing']['widget'],
		)
		self.auth_token = config['dashing']['auth_token']

		self.req = urllib2.Request(self.url)
		self.req.add_header('Content-Type', 'application/json')

	def on_start(self):
		logger.debug(self.url)

	def on_stop(self):
		self.send_stopped()

	def send_stopped(self):
		message = json.dumps({
			"auth_token": self.auth_token,
			"title": "Radio down :(",
			"text":""
		})
		logger.info(message)
		self.send_to_dashing(message)

	def track_playback_started(self, tl_track):
		current_track = tl_track.track
		current_track = "None" if tl_track is None else self.title_dash_artist(current_track)

		message = json.dumps({
			"auth_token": self.auth_token,
			"title": "Currently playing",
			"text": current_track
		}, cls=ModelJSONEncoder)

		logger.info(message)
		self.send_to_dashing(message)

	def send_to_dashing(self, message):
		try:
			response = requests.post(
				self.url,
				data=message,
			)
		except Exception as e:
			logger.warning('Unable to send webhook: ({1}) {2}'.format(
				e.__class__.__name__,
				e.message,
			))
		else:
			logger.debug('Webhook response: ({0}) {1}'.format(
				response.status_code,
				response.text,
			))

	def title_dash_artist(self,track):
		if len(track.artists) < 1:
			return track.name
		return track.name + " - " + iter(track.artists).next().name

