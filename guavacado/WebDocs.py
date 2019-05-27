#! /usr/bin/env python

# WebDocs.py
# defines:
#	WebDocs
#
# made by Joshua Huseman, jhuseman@alumni.nd.edu

import importlib # using importlib for some imports to stop warnings from IDE about missing modules
guavacado_version = importlib.import_module("guavacado.version_number").guavacado_version
WebServerNameAndVer = "Guavacado/"+guavacado_version

from guavacado.WebInterface import WebInterface
from guavacado.misc import generate_redirect_page

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

class WebDocs(WebInterface):
	'''provides a documentation page for the web server, showing all functions available and their URLs'''
	def __init__(self,host):
		self.host = host
		# self.connect('/','ROOT_REDIRECT','GET')
		self.connect('/docs/','GET_DOCS','GET')
		self.connect('/docs/json/','GET_DOCS_JSON','GET')

	def ROOT_REDIRECT(self):
		"""redirects to /static/ directory"""
		return generate_redirect_page("/static/")

	def GET_DOCS(self):
		"""return the documentation page in HTML format"""
		resources = ""
		for resource in self.host.resource_list:
			if resource["docstring"] is None:
				resource["docstring"] = "&lt;No docs provided!&gt;"
			resource_html = """
				<tr>
					<td><a href="{resource}">{resource}</a></td>
					<td>{method}</td>
					<td>{function_name}</td>
					<td>{docstring}</td>
				</tr>
			""".format(
				resource = resource["resource"],
				method = resource["method"],
				function_name = resource["function_name"],
				docstring = resource["docstring"].replace("\n","<br />"),
			)
			resources = resources+resource_html
		return """
			<!DOCTYPE html>
			<html>
				<head>
					<title>Guavacado Web Documentation</title>
				</head>
				<body>
					<table border="1">
						<tr>
							<th>Resource</th>
							<th>Method</th>
							<th>Function Name</th>
							<th>Docstring</th>
						</tr>
						{resources}
					</table>
				</body>
			</html>
		""".format(resources=resources)

	def GET_DOCS_JSON(self):
		"""return the documentation page in JSON format"""
		return json.dumps(self.host.resource_list)
