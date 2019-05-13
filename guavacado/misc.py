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

def generate_redirect_page(dest):
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

