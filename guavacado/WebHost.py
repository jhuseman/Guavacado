#! /usr/bin/env python

# WebHost.py
# defines:
#	WebHost
#
# made by Joshua Huseman, jhuseman@alumni.nd.edu

from .WebDocs import WebDocs
from .WebDispatcher import WebDispatcher
from .misc import init_logger, set_loglevel, addr_rep

class WebHost(object):
	'''
		class for hosting a "/static" folder
		allows WebInterface objects to serve dynamic content alongside the "/static" folder
	'''
	#TODO: figure out if host=None works from external to network
	def __init__(self,addr=[((None,80),None)],timeout=10,loglevel='INFO',staticdir="static",staticindex="index.html",include_fp=['{staticdir}/*'],exclude_fp=[], error_404_page_func=None):
		set_loglevel(loglevel)
		self.log_handler = init_logger(__name__)
		self.addr=addr
		self.dispatcher = WebDispatcher(addr=self.addr, timeout=timeout, staticdir=staticdir, staticindex=staticindex,include_fp=include_fp,exclude_fp=exclude_fp, error_404_page_func=error_404_page_func)

		self.resource_list = []
		self.docs = WebDocs(self)

	def start_service(self):
		self.log_handler.info('Starting web server on {addr}'.format(addr=addr_rep(self.addr)))
		self.log_handler.debug("All Resources: {}".format(self.resource_list))
		self.dispatcher.start_service()
	
	def stop_service(self):
		self.log_handler.info('Stopping web server on {addr}'.format(addr=addr_rep(self.addr)))
		self.dispatcher.stop_service()
		self.log_handler.info('Web server stopped on {addr}'.format(addr=addr_rep(self.addr)))

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
