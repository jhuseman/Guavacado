#! /usr/bin/env python

from .misc import init_logger

class RawSocketDispatcher(object):
	'''a dispatcher to simply call a callback function on each connection'''
	def __init__(self, callback):
		self.log_handler = init_logger(__name__)
		self.callback = callback

	def handle_connection(self, clientsocket, address, client_id):
		self.callback(clientsocket, address, client_id)
