#! /usr/bin/env python

# WebDispatcher.py
# defines:
#	WebDispatcher
#
# made by Joshua Huseman, jhuseman@alumni.nd.edu

from .version_number import guavacado_version
WebServerNameAndVer = "Guavacado/"+guavacado_version

from .misc import generate_redirect_page, init_logger, url_decode, addr_rep
from .ConnListener import ConnListener
from .WebRequestHandler import WebRequestHandler

from datetime import datetime
import os
import threading
import fnmatch

class WebDispatcher(object):
	'''handles requests by identifying function based on the URL, then dispatching the request to the appropriate function'''
	#TODO: figure out if host=None works from external to network
	def __init__(self, addr=None, timeout=None, staticdir="static", staticindex="index.html", include_fp=['{staticdir}/*'], exclude_fp=[], error_404_page_func=None):
		self.log_handler = init_logger(__name__)
		self.addr = addr
		self.timeout = timeout
		self.staticdir = staticdir
		self.staticindex = staticindex
		self.include_fp = include_fp
		self.exclude_fp = exclude_fp
		self.error_404_page_func = error_404_page_func
		self.resource_dict = {}
		self.set_default_handler("GET", self.default_GET_handler)
		self.create_conn_listeners()
	
	def create_conn_listeners(self):
		self.conn_listeners = []
		for addr in self.addr:
			self.conn_listeners.append({'listener':ConnListener(self.handle_connection, addr=addr), 'addr':addr})

	def handle_connection(self, clientsocket, address, client_id):
		handler = WebRequestHandler(clientsocket, address, client_id, self.request_handler, timeout=self.timeout)
		handler.handle_connection()

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
		if method not in self.resource_dict:
			self.resource_dict[method] = {'default':None,'resources':{}}

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

	def start_service(self):
		for listener in self.conn_listeners:
			self.log_handler.debug('Starting connection listener for {addr}'.format(addr=addr_rep(listener['addr'])))
			listener['thread'] = threading.Thread(target=listener['listener'].run, name='conn_listener_{addr}'.format(addr=addr_rep(listener['addr'])))
			listener['thread'].daemon = True
			listener['thread'].start()
	
	def stop_service(self):
		for listener in self.conn_listeners:
			self.log_handler.debug('Stopping connection listener for {addr}'.format(addr=addr_rep(listener['addr'])))
			listener['listener'].stop()
			listener['thread'].join(60)
			if listener['thread'].is_alive():
				self.log_handler.warn('Continuing without closing connection listener thread for {addr} because it did not close!'.format(addr=addr_rep(listener['addr'])))
			else:
				self.log_handler.debug('Stopped connection listener for {addr}'.format(addr=addr_rep(listener['addr'])))

	def get_address_string(self):
		return "{server} Server at {addr}".format(server=WebServerNameAndVer, addr=addr_rep(self.addr, pretty=True))
	
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
