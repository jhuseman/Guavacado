#! /usr/bin/env python

from .WebInterface import WebInterface
from .misc import generate_redirect_page

import json

class WebDocs(WebInterface):
	'''provides a documentation page for the web server, showing all functions available and their URLs'''
	def __init__(self, host, dispatcher_level=None):
		self.host = host
		WebInterface.__init__(self, host=self.host, dispatcher_level=dispatcher_level)
		self.resource_list = []
	
	def connect_funcs(self):
		# self.connect('/','ROOT_REDIRECT','GET')
		self.connect('/docs/','GET_DOCS','GET')
		self.connect('/docs/json/','GET_DOCS_JSON','GET')

	def log_connection(self,resource,action,method):
		log_entry = {
			"docstring":action.__doc__,
			"function_name":action.__name__,
			"resource":resource,
			"method":method,
		}
		self.resource_list.append(log_entry)

	def ROOT_REDIRECT(self):
		"""redirects to /static/ directory"""
		return generate_redirect_page("/static/")

	def GET_DOCS(self):
		"""return the documentation page in HTML format"""
		resources = ""
		for resource in self.resource_list:
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
		return json.dumps(self.resource_list)
