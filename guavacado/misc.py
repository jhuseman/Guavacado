#! /usr/bin/env python

# misc.py
# defines:
#	generate_redirect_page
#
# made by Joshua Huseman, jhuseman@alumni.nd.edu

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

