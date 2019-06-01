#! /usr/bin/env python

# misc.py
# defines:
#	generate_redirect_page
#	set_loglevel
#	init_logger
#	addr_rep
#	url_decode
#
# made by Joshua Huseman, jhuseman@alumni.nd.edu

import logging
import sys
import urllib

def generate_redirect_page(dest):
	'''returns a minimal HTML redirect page to quickly redirect the web browser to a specified destination'''
	return """
		<!DOCTYPE html>
		<html>
			<head>
				<META http-equiv="refresh" content="0;URL={dest}">
				<title>Guavacado Web Redirect</title>
			</head>
			<body>
				There is no information at this page.
				If you are not redirected to {dest} immediately, you can click <a href="{dest}">here</a>.
				<script>
					window.location = "{dest}";
					window.location.replace("{dest}");
					window.location.href = "{dest}";
				</script>
			</body>
		</html>
	""".format(dest=dest)

ALL_LOGGER_NAMES = []
CURRENT_LOGLEVEL = logging.NOTSET

def set_loglevel(levelstr):
	global CURRENT_LOGLEVEL
	global ALL_LOGGER_NAMES
	if levelstr is None:
		level = None
	elif isinstance(levelstr, int):
		level = levelstr
	else:
		level = getattr(logging, levelstr, None)
	if level is None:
		extra_levels = {}
		if levelstr in extra_levels:
			level = extra_levels[levelstr]
		else:
			level = 1000000
	CURRENT_LOGLEVEL = level
	for logname in ALL_LOGGER_NAMES:
		logger = logging.getLogger(logname)
		logger.setLevel(CURRENT_LOGLEVEL)

def init_logger(name):
	global CURRENT_LOGLEVEL
	global ALL_LOGGER_NAMES
	fmt = '%(asctime)s | %(levelname)-8s | %(filename)-20s | line:%(lineno)-3s | %(message)s'
	logger = logging.getLogger(name)
	if not name in ALL_LOGGER_NAMES:
		ALL_LOGGER_NAMES.append(name)
		logger.setLevel(CURRENT_LOGLEVEL)
		handler = logging.StreamHandler(sys.stdout)
		formatter = logging.Formatter(fmt)
		handler.setFormatter(formatter)
		logger.addHandler(handler)
	return logger

def addr_rep(addr, pretty=False):
	def tls_rep(addr):
		if addr is None:
			return 'disabled'
		if type(addr) in [tuple]:
			return 'cert:{cert},key:{key}'.format(cert=addr[0],key=addr[1])
	if type(addr) in [list]:
		if len(addr)==1:
			return addr_rep(addr[0])
		else:
			if pretty:
				if len(addr) > 2:
					return ', '.join([addr_rep(a,pretty=True) for a in addr[:-1]])+', and '+addr_rep(addr[-1],pretty=True)
				else:
					return ' and '.join([addr_rep(a,pretty=True) for a in addr])
			else:
				return '[{}]'.format(','.join([addr_rep(a) for a in addr]))
	elif type(addr) in [tuple]:
		if addr[0] is None:
			return addr_rep(('',addr[1]))
		elif type(addr[0]) in [tuple]:
			if addr[1] is None:
				return addr_rep(addr[0])
			else:
				if pretty:
					return '{addr} (https)'.format(addr=addr_rep(addr[0],pretty=True))
				else:
					return '{addr}(tls:[{tls}])'.format(addr=addr_rep(addr[0]),tls=tls_rep(addr[1]))
		else:
			if pretty:
				return '{ip} port {port}'.format(ip=addr[0], port=addr[1])
			else:
				return '{ip}:{port}'.format(ip=addr[0], port=addr[1])
	else:
		if pretty:
			return ''
		else:
			return str(addr)

def url_decode(url):
	urllib_parse = getattr(urllib,'parse',urllib)
	return urllib_parse.unquote(url)
