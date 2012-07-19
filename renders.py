#!/usr/bin/python
# -*- encoding: utf-8 -*-

 # * Copyright (c) 2012 Christopher Ramírez blindedbythedark [at} gmail (dot] com.
 # * All rights reserved.
 # *  
 # * Permission is hereby granted, free of charge, to any person obtaining a
 # * copy of this software and associated documentation files (the "Software"), 
 # * to deal in the Software without restriction, including without limitation 
 # * the rights to use, copy, modify, merge, publish, distribute, sublicense, 
 # * and/or sell copies of the Software, and to permit persons to whom the 
 # * Software is furnished to do so, subject to the following conditions:
 # *  
 # * The above copyright notice and this permission notice shall be included in
 # * all copies or substantial portions of the Software.
 # *  
 # * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 # * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
 # * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 # * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
 # * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
 # * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER 
 # * DEALINGS IN THE SOFTWARE.

"""
Secretary
Take the power of Django or Jinja2 templates to OpenOffice and LibreOffice.

This file implements BaseRender. BaseRender prepares a XML which describes
ODT document content to be processed by jinja2 or Django template system.  
"""

import re
import os
import zipfile
import xml.dom.minidom
from jinja2 import Template as TemplateEngine


class BaseRender():
	"""
		Prapares a XML string or file to be processed by a templating system.
		
		Use example:
		render = BaseRender('content/xml', var1, var2.. varN)
		render.render
	"""

	def __init__(self, xml_doc, **template_args):
		self.template_vars = template_args
		self.xml_document = xml.dom.minidom.parse(xml_doc)
		body = self.xml_document.getElementsByTagName('office:body')
		self.content_body = body and body[0]

	# ------------------------------------------------------------------------@

	def render_with_engine(self):
		"""
			Once the XML have been prepared, this routine is called
			to do the actual rendering.
		"""
		template = TemplateEngine(self.content_body.toxml())
		return template.render(**self.template_vars)


	def render(self):
		"""
			render prepares the XML and the call render_with_engine
			to parse template engine tags
		"""
		# TODO:
		# Prepare {% blocks|if|for|etc %} for rendering
		return self.render_with_engine()


if __name__ == "__main__":
	print 'Testing with content.xml\n'

	render = BaseRender('content.xml', name='Christopher')
	print render.render()

	# xml_document = xml.dom.minidom.parse('content.xml')
	# doc_body = xml_document.getElementsByTagName('office:body')
	# doc_body = doc_body and doc_body[0]

	# template = Template(doc_body.toprettyxml())

	# print template.render( name='Christopher :)' )


    
    
