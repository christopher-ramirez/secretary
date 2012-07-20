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


try:
    from jinja2 import Template as TemplateEngine
except ImportError:
    from django.template import Template as TemplateEngine


PARAGRAPH_TAG = '{% paragraph_tag %}'

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


    def get_paragraph_parent(self, node):
        """
            Returns the first node's parent with name "text:p"
            If parent "text:p" is not found, returns None.
        """

        if hasattr(node, 'parentNode'):
            if node.parentNode.nodeName.lower() == 'text:p':
                return node.parentNode
            else:
                return get_paragraph_parent(node.parentNode)
        else:
            return None

    # ------------------------------------------------------------------------@


    def render_with_engine(self):
        """
            Once the XML have been prepared, this routine is called
            to do the actual rendering.
        """
        template = TemplateEngine(self.xml_document.toxml())
        return template.render(**self.template_vars)

    # -----------------------------------------------------------------------


    def scan_child_nodes(self, nodes):
        """

        """
        if nodes.hasChildNodes():
            child_nodes = nodes.childNodes

            for node in child_nodes:
                if node.nodeType == node.TEXT_NODE:
                    node_text = node.data.lower()

                    # replace a paragraph node with contained tags
                    # if tag PARAGRAPH_TAG is in paragraph content.

                    if node_text.find(PARAGRAPH_TAG) > -1:
                        # Get this node text:p parent
                        paragraph_node = self.get_paragraph_parent(node)
                        paragraph_parent = paragraph_node.parentNode


                        # Discar PARAGRAPH_TAG
                        pgraph_node_text = \
                            paragraph_node.toxml().replace(PARAGRAPH_TAG, '')

                        # replace text:p node's XML with its contained templates tags.
                        new_node_text = \
                            ' '.join(re.findall('(\{.*?\})', pgraph_node_text))

                        new_node = xml_document.createTextNode(new_node_text)
                        paragraph_parent.replaceChild(new_node, paragraph_node)

                else:
                    if node.hasChildNodes():
                        scan_child_nodes(node)

    # -----------------------------------------------------------------------


    def handle_special_tags(self):
        """

        """
        paragraphs = self.content_body.getElementsByTagName('text:p')
        for paragraph in paragraphs:
            self.scan_child_nodes(paragraph)

    # -----------------------------------------------------------------------


    def render(self):
        """
            render prepares the XML and the call render_with_engine
            to parse template engine tags
        """
        
        self.handle_special_tags()

        return self.render_with_engine()

    # -----------------------------------------------------------------------
    

if __name__ == "__main__":

    data = {
        'name': u'Christopher Ramirez',
        'country': 'Nicaragua'
    }

    render = BaseRender('content.xml', record=data)
    print render.render()

    # xml_document = xml.dom.minidom.parse('content.xml')
    # doc_body = xml_document.getElementsByTagName('office:body')
    # doc_body = doc_body and doc_body[0]

    # template = Template(doc_body.toprettyxml())

    # print template.render( name='Christopher :)' )


    
    
