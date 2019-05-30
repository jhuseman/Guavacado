#! /usr/bin/env python

# WebHost.py
# defines:
#	WebHost
#
# made by Joshua Huseman, jhuseman@alumni.nd.edu

from .WebDocs import WebDocs
from .WebDispatcher import WebDispatcher

class WebHost(object):
	'''
		class for hosting a "/static" folder
		allows WebInterface objects to serve dynamic content alongside the "/static" folder
	'''
	#TODO: figure out if host=None works from external to network
	def __init__(self,port=80,host='0.0.0.0',staticdir="static",staticindex="index.html",include_fp=['{staticdir}/*'],exclude_fp=[], error_404_page_func=None):
		self.port = port
		self.host = host
		self.dispatcher = WebDispatcher(host=self.host, port=self.port, staticdir=staticdir, staticindex=staticindex,include_fp=include_fp,exclude_fp=exclude_fp, error_404_page_func=error_404_page_func)

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
