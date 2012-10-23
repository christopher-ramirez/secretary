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
import StringIO
import xml.dom.minidom


try:
    from jinja2 import Template as TemplateEngine
except ImportError:
    from django.template import Template as TemplateEngine


PARAGRAPH_TAG = '{% control_paragraph %}'
TABLEROW_TAG = '{% control_tablerow %}'
TABLECELL_TAG = '{% control_tablecell %}'

OOO_PARAGRAPH_NODE = 'text:p'
OOO_TABLEROW_NODE = 'table:table-row'
OOO_TABLECELL_NODE = 'table:table-cell'

class BaseRender():
    """
        Prapares a XML string or file to be processed by a templating system.
        
        Use example:
        render = BaseRender('content/xml', var1, var2.. varN)
        render.render
    """

    def __init__(self, xml_doc, **template_args):
        self.template_vars = template_args
        self.xml_document = xml.dom.minidom.parseString(xml_doc)
        body = self.xml_document.getElementsByTagName('office:body')
        self.content_body = body and body[0]

    # ------------------------------------------------------------------------@


    def get_parent_of(self, node, parent_type):
        """
            Returns the first node's parent with name  of parent_type
            If parent "text:p" is not found, returns None.
        """

        if hasattr(node, 'parentNode'):
            if node.parentNode.nodeName.lower() == parent_type:
                return node.parentNode
            else:
                return self.get_parent_of(node.parentNode, parent_type)
        else:
            return None

    # ------------------------------------------------------------------------@


    def render_with_engine(self):
        """
            Once the XML have been prepared, this routine is called
            to do the actual rendering.
        """
        
        template = TemplateEngine(self.xml_document.toprettyxml())
        return template.render(**self.template_vars)


    # -----------------------------------------------------------------------


    def prepare_document(self):
        """
            Search in every paragraph node in the document.
        """
        paragraphs = self.content_body.getElementsByTagName('text:p')
        
        for paragraph in paragraphs:
            self.scan_paragraph_child_nodes(paragraph)
            

    def scan_paragraph_child_nodes(self, nodes):
        """

        """

        if nodes.hasChildNodes():
            child_nodes = nodes.childNodes

            for node in child_nodes:
                if node.nodeType == node.TEXT_NODE:
                    self.handle_special_tags(node)
                else:
                    if node.hasChildNodes():
                        self.scan_paragraph_child_nodes(node)

    # -----------------------------------------------------------------------


    def handle_special_tags(self, node):
        """

        """
        node_text = node.data.lower()
        replace_node = None

        if node_text.find(PARAGRAPH_TAG) > -1:
            replace_node = self.get_parent_of(node, OOO_PARAGRAPH_NODE)
            note_text = replace_node.toxml().replace(PARAGRAPH_TAG, '')

        elif node_text.find(TABLEROW_TAG) > -1:
            replace_node = self.get_parent_of(node, OOO_TABLEROW_NODE)
            note_text = replace_node.toxml().replace(TABLEROW_TAG, '')

        elif node_text.find(TABLECELL_TAG) > -1:
            replace_node = self.get_parent_of(node, OOO_TABLECELL_NODE)
            note_text = replace_node.toxml().replace(TABLECELL_TAG, '')




        if replace_node is not None:
            paragraph_parent = replace_node.parentNode

            new_node_text = \
                ' '.join(re.findall('(\{.*?\})', note_text))

            new_node = self.xml_document.createTextNode(new_node_text)
            paragraph_parent.replaceChild(new_node, replace_node)

    # -----------------------------------------------------------------------


    def render(self):
        """
            render prepares the XML and the call render_with_engine
            to parse template engine tags
        """
        
        self.prepare_document()
        return self.render_with_engine()

    # -----------------------------------------------------------------------



def render_template(template, **template_args):
    """
        Renders *template* file using *template_args* variables.
        Returns the ODF file generated.
    """
    
    input = zipfile.ZipFile(template, "r" )
    text = StringIO.StringIO()
    output = zipfile.ZipFile(text, 'a')
       
    # go through the files in source
    for zi in input.filelist:
        out = input.read( zi.filename )

        if zi.filename == 'content.xml':
            render = BaseRender(out, **template_args)
            out = render.render().encode('ascii', 'xmlcharrefreplace')

        elif zi.filename == 'mimetype':
            # mimetype is stored within the ODF
            mimetype = out 

        output.writestr(zi.filename, out, zipfile.ZIP_DEFLATED)

    # close and finish
    input.close()
    output.close()
    
    return text.getvalue()


if __name__ == "__main__":

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


    # ODF is just a zipfile
    input = zipfile.ZipFile( 'simple_template.odt', "r" )

    # we cannot write directly to HttpResponse, so use StringIO
    # text = StringIO.StringIO()
    text = open('rendered.odt', 'wb')
    # output document
    output = zipfile.ZipFile( text, "w" )
       
    # go through the files in source
    for zi in input.filelist:
        out = input.read( zi.filename )

        if zi.filename == 'content.xml':
            render = BaseRender(out, trademark={'owner':{}}, document=document, countries=countries)
            out = render.render().encode('ascii', 'xmlcharrefreplace')

        elif zi.filename == 'mimetype':
            # mimetype is stored within the ODF
            mimetype = out 

        output.writestr( zi.filename, out,
                         zipfile.ZIP_DEFLATED )

    # close and finish
    input.close()
    output.close()

    print "Template rendering finished! Check rendered.odt file."

    # output_file.open('rendered.odt', 'w')
    # output_file.write(output)
    # output_file.close()

    # render = BaseRender('content.xml', record=data)
    # print render.render()

    # xml_document = xml.dom.minidom.parse('content.xml')
    # doc_body = xml_document.getElementsByTagName('office:body')
    # doc_body = doc_body and doc_body[0]

    # template = Template(doc_body.toprettyxml())

    # print template.render( name='Christopher :)' )


    
    
