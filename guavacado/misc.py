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
	fmt = '%(asctime)s | %(levelname)-8s | %(filename)-20s | line:%(lineno)-3s | %(message)s'
	logger = logging.getLogger(name)
	handler = logging.StreamHandler(sys.stdout)
	formatter = logging.Formatter(fmt)
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	if not name in ALL_LOGGER_NAMES:
		ALL_LOGGER_NAMES.append(name)
		logger.setLevel(CURRENT_LOGLEVEL)
	return logger

def addr_rep(addr):
	if addr[0] is None:
		return addr_rep(['']+list(addr[1:]))
	return '{ip}:{port}'.format(ip=addr[0], port=addr[1])

def url_decode(url):
	urllib_parse = getattr(urllib,'parse',urllib)
	return urllib_parse.unquote(url)
