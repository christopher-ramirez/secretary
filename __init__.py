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
Take the power of Jinja2 templates to OpenOffice and LibreOffice.

This file implements BaseRender. BaseRender prepares a XML which describes
ODT document content to be processed by jinja2 or Django template system.  
"""

import re
import os
import sys
import logging
import zipfile
import StringIO
import xml.dom.minidom
from os.path import isfile
from jinja2 import Environment, Undefined


PARAGRAPH_TAG = '{% control_paragraph %}'
TABLEROW_TAG = '{% control_tablerow %}'
TABLECELL_TAG = '{% control_tablecell %}'

ODF_PARAGRAPH_NODE = 'text:p'
ODF_TABLEROW_NODE = 'table:table-row'
ODF_TABLECELL_NODE = 'table:table-cell'


class UndefinedSilently(Undefined):
    # Silently undefined,
    # see http://stackoverflow.com/questions/6182498/jinja2-how-to-make-it-fail-silently-like-djangotemplate
    def silently_undefined(*args, **kwargs):
        return u''

    return_new = lambda *args, **kwargs: UndefinedSilently()

    __unicode__ = silently_undefined
    __str__ = silently_undefined
    __call__ = return_new
    __getattr__ = return_new

# ************************************************
# 
#           SECRETARY FILTERS
# 
# ************************************************

def pad_string(value, length=5):
    value = str(value)
    return value.zfill(length)


class Render():
    """
        Prapares a XML string or file to be processed by a templating system.
        
        Use example:
        render = BaseRender('content/xml', var1, var2.. varN)
        render.render
    """

    _template = None
    _environment = None
    _working_template = None
    _unpacked_template = None
    _packed_template = None
    _content_file = None
    _style_file = None
    _mimetype = ''


    @property
    def enviroment(self):
        return self._environment
    @enviroment.setter
    def enviroment(self, value):
        self._environment = value

    @property
    def template(self):
        return self._template
    @template.setter
    def template(self, value):
        self._template = value


    # def __init__(self, xml_doc, template_args):
    def __init__(self, template, **kwargs):
        """
        Builds a ODFRender instance
        TODO: document
        """

        self.template = template
        self._environment = Environment(undefined=UndefinedSilently)
        self._environment.filters['pad'] = pad_string 

    
    def unpack_template(self):
        """
            Loads the template into a ZIP file, allowing to make
            CRUD operations into the ZIP archive.
        """

        if os.path.exists(self.template):
            f = open(self.template, 'r')
            self._unpacked_template = zipfile.ZipFile(f, "r" )
        else:
            self._unpacked_template = zipfile.ZipFile(self._template, "r" )
        
        # go through the files in source
        for zi in self._unpacked_template.filelist:
            archive_file = self._unpacked_template.read( zi.filename )

            if zi.filename == 'content.xml':
                self._content_file = archive_file
            elif zi.filename == 'styles.xml':
                self._style_file = archive_file
            elif zi.filename == 'mimetype':
                self._mimetype = archive_file

    def pack_document(self):
        """
            Make an archive from _unpacked_template
        """
        self.rendered = StringIO.StringIO()
        self._packed_template = zipfile.ZipFile(self.rendered, 'a')

        for zip_file in self._unpacked_template.filelist:
            out = self._unpacked_template.read( zip_file.filename )

            if zip_file.filename == 'mimetype':
                # mimetype is stored within the ODF
                mimetype = self._mimetype

            if zip_file.filename == 'content.xml':
                out = self._content_file

            if zip_file.filename == 'styles.xml':
                out = self._style_file

            if sys.version_info >= (2, 7):
                self._packed_template.writestr(zip_file.filename, out, zipfile.ZIP_DEFLATED)
            else:
                self._packed_template.writestr(zip_file.filename, out)

        self._packed_template.close()
        self._unpacked_template.close()


    def render(self, **kwargs):
        """
            Unpack and render the internal template
        """

        self.unpack_template()
        self._template_vars = kwargs

        # Load content.xml and style.xml file
        self.content = xml.dom.minidom.parseString(self._content_file)
        body = self.content.getElementsByTagName('office:body')
        self.content_body = body and body[0]

        self.styles = xml.dom.minidom.parseString(self._style_file)
        body = self.styles.getElementsByTagName('office:master-styles')
        self.headers = body and body[0]

        # Render content.xml
        self.prepare_template_tags(self.content_body)
        template = self._environment.from_string(self.content.toxml())
        result = template.render(**kwargs)
        result = result.replace('\n', '<text:line-break/>')
        self.content = xml.dom.minidom.parseString(result.encode('ascii', 'xmlcharrefreplace'))
        self.content_body = self.content.getElementsByTagName('office:body')

        # Render style.xml
        self.prepare_template_tags(self.styles)
        template = self._environment.from_string(self.styles.toxml())
        result = template.render(**kwargs)
        result = result.replace('\n', '<text:line-break/>')
        self.styles = xml.dom.minidom.parseString(result.encode('ascii', 'xmlcharrefreplace'))
        self.headers = None

        # Save rendered content and headers
        self._content_file = self.content.toxml().encode('ascii', 'xmlcharrefreplace')

        self._style_file = (self.styles.toxml().encode('ascii', 'xmlcharrefreplace'))

        self.pack_document()
        return self.rendered

    
    def node_parents(self, node, parent_type):
        """
            Returns the first node's parent with name  of parent_type
            If parent "text:p" is not found, returns None.
        """

        if hasattr(node, 'parentNode'):
            if node.parentNode.nodeName.lower() == parent_type:
                return node.parentNode
            else:
                return self.node_parents(node.parentNode, parent_type)
        else:
            return None


    def create_text_span_node(self, xml_document, content):
        span = self.content.createElement('text:span')
        text_node = self.create_text_node(self.content, content)
        span.appendChild(text_node)

        return span

    def create_text_node(self, xml_document, text):
        """
        Creates a text node
        """
        return self.content.createTextNode(text)


    def prepare_template_tags(self, xml_document):
        """
            Search every field node in the inner template and
            replace them with a <text:span> field. Flow tags are
            replaced with a blank node and moved into the ancestor
            tag defined in description field attribute.
        """
        fields = xml_document.getElementsByTagName('text:text-input')

        for field in fields:
            if field.hasChildNodes():
                field_content = field.childNodes[0].data.replace('\n', '')

                jinja_tags = re.findall(r'(\{.*?\}*})', field_content)
                if not jinja_tags:
                    # Field does not contains jinja template tags
                    continue

                field_description = field.getAttribute('text:description')

                if not field_description:
                    new_node = self.create_text_span_node(xml_document, field_content)
                else:
                    if field_description in \
                        ['text:p', 'table:table-row', 'table:table-cell']:
                        field = self.node_parents(field, field_description)

                    new_node = self.create_text_node(xml_document, field_content)

                parent = field.parentNode
                parent.insertBefore(new_node, field)
                parent.removeChild(field)
            

def render_template(template, **kwargs):
    """
        Render a ODF template file
    """

    engine = Render(file)
    return engine.render(**kwargs)


if __name__ == "__main__":
    from sys import argv
    from datetime import datetime

    document = {
        'datetime': datetime.now()
    }

    countries = [
        {'country': 'United States', 'capital': 'Washington', 'cities': ['miami', 'new york', 'california', 'texas', 'atlanta']},
        {'country': 'England', 'capital': 'London', 'cities': ['gales']},
        {'country': 'Japan', 'capital': 'Tokio', 'cities': ['hiroshima', 'nagazaki']},
        {'country': 'Nicaragua', 'capital': 'Managua', 'cities': [u'león', 'granada', 'masaya']},
        {'country': 'Argentina', 'capital': 'Buenos aires'},
        {'country': 'Chile', 'capital': 'Santiago'},
        {'country': 'Mexico', 'capital': 'MExico City', 'cities': ['puebla', 'cancun']},
    ]


    render = Render('simple_template.odt')
    result = render.render(countries=countries, document=document)
    
    output = open('rendered.odt', 'w')
    output.write(result.getvalue())

    print "Template rendering finished! Check rendered.odt file."