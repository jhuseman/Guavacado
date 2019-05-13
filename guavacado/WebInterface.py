#! /usr/bin/env python

# Guavacado.py
# defines:
#	WebHost:
#		cherrypy wrapper for hosting a "/static" folder
#		allows WebInterface objects to serve dynamic content
#		  alongside the "/static" folder
#	WebInterface:
#		"purely virtual" class for a dynamic web interface
#
# made by Joshua Huseman, jhuseman@alumni.nd.edu
# Created: 06/08/2016 [0.1.0]
# Updated: 06/13/2016 [0.2.0]
# Updated: 08/01/2017 [0.3.0] - removed logging to screen
# Updated: 06/16/2018 [1.0.0] - removed cherrypy dependency, instead using python built-in BaseHTTPServer
# Updated: 02/08/2019 [1.0.1] - added check in "connect" function to operate just like "connect_callback" with function argument, added optional argument to WebInterface to specify host or host arguments
# Updated: 02/13/2019 [1.0.2] - added request on "stop_service" function to force server to finish run loop
# CRITICAL UPDATE: 02/13/2019 [1.0.3] - fixed bug allowing access to entire contents of drive upon opening url //
# Updated: 02/14/2019 [1.0.4] - added include_fp and exclude_fp parameters to specify lists of directories or file patterns that can be accessed by the server
# Updated: 02/22/2019 [1.1.0] - added full support for python3
# Updated: 02/22/2019 [1.1.1] - fixed bug showing strange backslash in redirect page on Windows
# Updated: 02/22/2019 [1.1.2] - added functionality to support the body of data in the first argument of a callback
# Updated: 03/10/2019 [1.1.2] - updated for standalone library, Guavacado rebrand

import importlib # using importlib for some imports to stop warnings from IDE about missing modules
guavacado_version = importlib.import_module("guavacado.version_number").guavacado_version
WebServerNameAndVer = "Guavacado/"+guavacado_version

from datetime import datetime
import mimetypes
import json
import os
import traceback
import fnmatch

import sys # only needed for python version check
if sys.version_info[0] < 3:
	# Python 2-specific imports and functions
	http_server = importlib.import_module("BaseHTTPServer")
	urllib = importlib.import_module("urllib")
	url_decode = urllib.unquote
	urlopen = urllib.urlopen
	def encode_to_send(s):
		return s
	def get_header(headers, header_name):
		return headers.getheader(header_name)
else:
	# Python 3-specific imports and functions
	import http.server as http_server
	from urllib.parse import unquote as url_decode
	from urllib.request import urlopen
	def encode_to_send(s):
		return s.encode('UTF-8')
	def parse_headers(headers):
		return dict([tuple(l.split(': ')[:2]) for l in str(headers).split('\n') if ': ' in l])
	def get_header(headers, header_name):
		return parse_headers(headers).get('Content-Length',None)

class WebInterface(object):
	"""
	Allows for easily defining web interfaces for the server.

	Expects the variable "self.host" to be set to a WebHost
	object before calling "connect()".

	See implementation of __init__ class for an example initialization.
	"""

	def __init__(self, host=None, host_kwargs={'port':80}):
		# starts a WebHost on port 80 that
		if host is None:
			from guavacado import WebHost
			self.host = WebHost(**host_kwargs)
		else:
			self.host = host

		# # add lines like the following:
		# self.connect('/test/:id','GET_ID','GET')
		# self.connect('/test/:id',self.GET_ID,'GET')
		# # to call member function GET_ID() with the argument after "/test/" when a GET request
		# # is received for "/test/<any text here>"
	
	def connect(self, resource, action, method, body_included=False):
		if isinstance(action, str):
			callback = getattr(self, action)
		else:
			callback = action
		self.connect_callback(resource, callback, method, body_included=body_included)
	
	def connect_callback(self,resource,callback,method, body_included=False):
		"""
		connects a specified callback (function) in this object
		to the specified resource (URL)
		and http method (GET/PUT/POST/DELETE)
		"""
		self.dispatcher = self.host.get_dispatcher()
		if body_included:
			disp_callback = callback
		else:
			def disp_callback(body, *args):
				return callback(*args)
		self.dispatcher.connect(resource, disp_callback, method)
		# log this connection on the host
		self.host.log_connection(resource,callback,method)
	def start_service(self):
		self.host.start_service()
	def stop_service(self):
		self.host.stop_service()
