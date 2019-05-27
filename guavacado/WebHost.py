#! /usr/bin/env python

# WebHost.py
# defines:
#	WebHost
#	WebDispatcher
#		WebRequestHandler
#
# made by Joshua Huseman, jhuseman@alumni.nd.edu

import importlib # using importlib for some imports to stop warnings from IDE about missing modules
guavacado_version = importlib.import_module("guavacado.version_number").guavacado_version
WebServerNameAndVer = "Guavacado/"+guavacado_version

from guavacado.misc import generate_redirect_page
from guavacado.WebDocs import WebDocs

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

class WebHost(object):
	'''
		class for hosting a "/static" folder
		allows WebInterface objects to serve dynamic content alongside the "/static" folder
	'''
	def __init__(self,port=80,host='0.0.0.0',log_function=None,staticdir="static",staticindex="index.html",include_fp=['{staticdir}/*'],exclude_fp=[], error_404_page_func=None):
		self.port = port
		self.host = host
		self.dispatcher = WebDispatcher(host=self.host, port=self.port, log_function=log_function, staticdir=staticdir, staticindex=staticindex,include_fp=include_fp,exclude_fp=exclude_fp, error_404_page_func=error_404_page_func)

		self.resource_list = []
		self.docs = WebDocs(self)

	def start_service(self):
		# # output resource list (for debug)
		# print "All Resources:"
		# print self.resource_list
		self.dispatcher.start_service()
	
	def stop_service(self):
		self.dispatcher.stop_service()

	def get_dispatcher(self):
		return self.dispatcher

	def log_connection(self,resource,action,method):
		log_entry = {
			"docstring":action.__doc__,
			"function_name":action.__name__,
			"resource":resource,
			"method":method,
		}
		self.resource_list.append(log_entry)

class WebDispatcher(object):
	'''handles requests by identifying function based on the URL, then dispatching the request to the appropriate function'''
	class WebRequestHandler(http_server.BaseHTTPRequestHandler):
		'''the internal request handler used by python's http_server'''
		def send_header_as_code(self, status_code, url):
			"""send the header of the response with the given status code"""
			mime_url = url
			if mime_url[-1]=='/':
				mime_url = url+"index.html"
			mime_type = mimetypes.MimeTypes().guess_type(mime_url)[0]
			if mime_type is None:
				mime_type = "text/html"
			self.send_response(status_code)
			self.send_header("Content-type", mime_type)
			self.end_headers()
		
		def do_HEAD(self):
			"""Respond to a HEAD request."""
			self.send_header_as_code(200, self.path)
		
		def GENERAL_REQ_HANDLER(self,callback):
			"""Respond to a GET request."""
			body_len_str = get_header(self.headers, 'Content-Length')
			if body_len_str is None:
				body_len = 0
				body = None
			else:
				body_len = int(body_len_str)
				body = self.rfile.read(body_len)
			try:
				ret_data = callback(url=self.path, method=self.command, headers=self.headers, body=body)
				if ret_data is None:
					self.send_header_as_code(404, '404.html')
					self.wfile.write(encode_to_send(self.get_404_page(url=self.path)))
				else:
					self.do_HEAD()
					self.wfile.write(encode_to_send(ret_data))
			except:
				tb = traceback.format_exc()
				self.send_header_as_code(500, '500.html')
				self.wfile.write(encode_to_send(self.get_500_page(tb=tb, url=self.path)))
		
		def log_message(self, format, *args):
			if not self.log_string is None:
				self.log_string("%s - - [%s] %s" %
					(self.client_address[0],
					self.log_date_time_string(),
					format%args))
		
		def log_string(self, data):
			print(data)
		
		def get_404_page(self, url=""):
			return ('<head><title>Error 404: Not Found</title></head>'+ \
			'<body><h1>Error response</h1><p>Error code 404.<p>Message: The URI "{url}" is not available.'+ \
			'<p>Error code explanation: 404 = Nothing matches the given URI.</body>').format(url=url)
		
		def get_500_page(self, tb="", url=""):
			return ('<head><title>Error 500: Internal Server Error</title></head>'+ \
			'<body><h1>Error response</h1><p>Error code 500.<p>Message: The server encountered an error processing the request "{url}".'+ \
			'<p>Error code explanation: <br /> <br />{tb}</body>').format(url=url, tb=tb.replace('\n','<br />\n'))
	
	def __init__(self, host="0.0.0.0", port=80, log_function=None, staticdir="static", staticindex="index.html", include_fp=['{staticdir}/*'], exclude_fp=[], error_404_page_func=None):
		self.host = host
		self.port = port
		self.log_function = log_function
		self.staticdir = staticdir
		self.staticindex = staticindex
		self.include_fp = include_fp
		self.exclude_fp = exclude_fp
		self.error_404_page_func = error_404_page_func
		self.request_handler_class = self.WebRequestHandler
		self.resource_dict = {}
		self.set_default_handler("GET", self.default_GET_handler)
		setattr(self.request_handler_class, 'log_string', classmethod(self.log_string))
		setattr(self.request_handler_class, 'get_404_page', classmethod(self.get_404_page))
		self.httpd = http_server.HTTPServer((self.host, self.port), self.request_handler_class)
	
	def split_url_params(self, url):
		split_url = url.split('/:')
		prefix = split_url[0]
		param_count = len(split_url)-1
		return (prefix, param_count)
	
	def get_possible_split_url_params(self, url):
		ret = []
		split_url = url.split('/')
		remaining = split_url
		removed = []
		while len(remaining)>0:
			prefix = '/'.join(remaining)
			param_count = len(split_url)-len(remaining)
			params = removed[:param_count]
			if (prefix+'/')==url:
				ret.append((prefix, param_count, params))
				param_count = param_count-1
				params = removed[:param_count]
			params_decoded = []
			for par in params:
				params_decoded.append(url_decode(par))
			ret.append((prefix, param_count, params_decoded))
			removed = [remaining[-1]] + removed
			remaining = remaining[:-1]
		return ret

	def connect(self, resource, callback, method):
		if method not in self.resource_dict:
			self.initialize_request_handler(method)
		(url_prefix, url_param_count) = self.split_url_params(resource)
		if url_prefix not in self.resource_dict[method]['resources']:
			self.resource_dict[method]['resources'][url_prefix] = {}
		self.resource_dict[method]['resources'][url_prefix][url_param_count] = callback
	
	def initialize_request_handler(self, method):
		def req_method_handler(request_handler_instance):
			self.request_handler_class.GENERAL_REQ_HANDLER(request_handler_instance, self.request_handler)
		if method not in self.resource_dict:
			self.resource_dict[method] = {'default':None,'resources':{}}
			do_command = 'do_'+method
			setattr(self.request_handler_class, do_command, req_method_handler)

	def request_handler(self, url=None, method=None, headers=None, body=None):
		if method in self.resource_dict:
			url_no_browseparams = url.split('?')[0] # remove and ignore anything after a question mark
			for (url_prefix, url_param_count, params) in self.get_possible_split_url_params(url_no_browseparams):
				if url_prefix in self.resource_dict[method]['resources']:
					if url_param_count in self.resource_dict[method]['resources'][url_prefix]:
						return self.resource_dict[method]['resources'][url_prefix][url_param_count](body, *params)
			if not self.resource_dict[method]['default'] is None:
				return self.resource_dict[method]['default'](url=url_no_browseparams, headers=headers, body=body)
		return None
	
	def set_default_handler(self, method, handler):
		if not method in self.resource_dict:
			self.initialize_request_handler(method)
		self.resource_dict[method]['default'] = handler
	
	def default_GET_handler(self, url=None, headers=None, body=None):
		url_relative = url[1:]
		while len(url_relative)>0 and url_relative[0]=='/':
			url_relative = url_relative[1:]
		index_relative = os.path.join(url_relative,self.staticindex)
		url_relative_static = os.path.join(self.staticdir,url_relative).replace('\\','/')
		index_relative_static = os.path.join(self.staticdir,index_relative).replace('\\','/')
		check_paths = [index_relative, url_relative, index_relative_static, url_relative_static]
		for path in check_paths:
			if self.check_path_allowed(path):
				if os.path.exists(path):
					if os.path.isfile(path):
						with open(path) as fp:
							data = fp.read()
						return data
					else:
						return self.get_dir_page(path)
		return None
	
	def check_path_allowed(self, path):
		for ex_fp in self.exclude_fp:
			if fnmatch.fnmatch(path, ex_fp.format(staticdir=self.staticdir, staticindex=self.staticindex)):
				return False
		for inc_fp in self.include_fp:
			if fnmatch.fnmatch(path, inc_fp.format(staticdir=self.staticdir, staticindex=self.staticindex)):
				return True
		return False
	
	def log_string(self, request_handler_instance, data):
		if not self.log_function is None:
			self.log_function(data)

	def start_service(self):
		self.service_running = True
		while self.service_running:
			self.httpd.handle_request()
		self.httpd.server_close()
		self.service_running = False
	
	def stop_service(self):
		self.service_running = False
		url = 'http://{host}:{port}/'.format(host='127.0.0.1',port=self.port)
		f = urlopen(url)
		f.read()
		f.close()
	
	def get_address_string(self):
		return "{server} Server at {host} Port {port}".format(server=WebServerNameAndVer, host=self.host, port=self.port)
	
	def get_dir_page(self, path):
		if path[-1]!='/':
			return generate_redirect_page('/'+path+'/')
		data = ('<html><head><title>Index of {path}</title></head><body><h1>Index of {path}</h1><table>'+\
			'<tr><th valign="top"></th><th>Name</th><th>Last modified</th><th>Size</th></tr>'+\
			'<tr><th colspan="5"><hr></th></tr>'+\
			'<tr><td valign="top"></td><td><a href="..">Parent Directory</a></td><td>&nbsp;</td><td align="right">  - </td></tr>').format(
				path="/"+path
			)
		for filename in os.listdir(path):
			fullpath = os.path.join(path,filename)
			if os.path.isdir(fullpath):
				if filename[-1]!='/':
					filename = filename + '/'
			filestat = os.stat(fullpath)
			size = filestat.st_size
			size_str = str(size)
			if size>(1<<10):
				size_str = str(size/(1<<10))+"K"
			if size>(1<<20):
				size_str = str(size/(1<<20))+"M"
			if size>(1<<30):
				size_str = str(size/(1<<30))+"G"
			if size>(1<<40):
				size_str = str(size/(1<<40))+"T"
			data = data + '<tr><td valign="top"></td><td><a href="{filename}">{filename}</a></td><td align="right">{lastmodified}</td><td align="right">{size}</td></tr>'.format(
				filename=filename,
				lastmodified=datetime.fromtimestamp(filestat.st_mtime),
				size=size_str
			)
		data = data + (('<tr><th colspan="5"><hr></th></tr></table>'+\
			'<address>{address}</address>'+\
			'</body></html>').format(
				address=self.get_address_string()
			))
		return data
	
	def get_404_page(self, request_handler_instance, url=""):
		if not self.error_404_page_func is None:
			return self.error_404_page_func(url=url)
		return ("<html><head><title>404 Not Found</title></head>"+\
		"<body><h1>Not Found</h1><p>The requested URL {url} was not found on this server.</p><hr>"+\
		"<address>{address}</address>"+\
		"</body></html>").format(url=url, address=self.get_address_string())

if __name__ == '__main__':
	"""
	serves only a static folder in the local 'static' directory
	"""
	host = WebHost(80)
	host.start_service()
