#!/usr/bin/python
# -*- encoding: utf-8 -*-

 # * Copyright (c) 2012 Christopher Ramírez chris.ramirezg [at} gmail (dot] com.
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

This file implements Render. Render provides an interface to render
Open Document Format (ODF) documents to be used as templates using
the jinja2 template engine. To render a template:
    engine = Render(template_file)
    result = engine.render(template_var1=...)
"""
from __future__ import unicode_literals, print_function

import re
import sys
import zipfile
import io
from xml.dom.minidom import parseString
from jinja2 import Environment, Undefined

# ---- Exceptions
class SecretaryError(Exception):
    pass

class UndefinedSilently(Undefined):
    # Silently undefined,
    # see http://stackoverflow.com/questions/6182498/jinja2-how-to-make-it-fail-silently-like-djangotemplate
    def silently_undefined(*args, **kwargs):
        return ''

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


class Render(object):
    """
        Main engine to convert and ODT document into a jinja
        compatible template.

        Basic use example:
            engine = Render('template')
            result = engine.render()


        Render provides an enviroment variable which can be used
        to provide custom filters to the ODF render.

            engine = Render('template.odt')
            engine.environment.filters['custom_filer'] = filter_function
            result = engine.render()
    """


    def __init__(self, template, **kwargs):
        """
        Builds a Render instance and assign init the internal enviroment.
        Params:
            template: Either the path to the file, or a file-like object.
                      If it is a path, the file will be open with mode read 'r'.
        """

        self.template = template
        self.environment = Environment(undefined=UndefinedSilently, autoescape=True)

        # Register provided filters
        self.environment.filters['pad'] = pad_string
        self.environment.filters['markdown'] = self.markdown_filter

        self.file_list = {}

    def unpack_template(self):
        """
            Loads the template into a ZIP file, allowing to make
            CRUD operations into the ZIP archive.
        """

        with zipfile.ZipFile(self.template, 'r') as unpacked_template:
            # go through the files in source
            for zi in unpacked_template.filelist:
                file_contents = unpacked_template.read( zi.filename )
                self.file_list[zi.filename] = file_contents

                if zi.filename == 'content.xml':
                    self.content = parseString( file_contents )
                elif zi.filename == 'styles.xml':
                    self.styles = parseString( file_contents )





    def pack_document(self):
        """
            Make an archive from _unpacked_template
        """

        # Save rendered content and headers
        self.rendered = io.BytesIO()

        with zipfile.ZipFile(self.rendered, 'a') as packed_template:
            for filename, content in self.file_list.items():
                if filename == 'content.xml':
                    content = self.content.toxml().encode('ascii', 'xmlcharrefreplace')

                if filename == 'styles.xml':
                    content = self.styles.toxml().encode('ascii', 'xmlcharrefreplace')

                if sys.version_info >= (2, 7):
                    packed_template.writestr(filename, content, zipfile.ZIP_DEFLATED)
                else:
                    packed_template.writestr(filename, content)




    def render(self, **kwargs):
        """
            Unpack and render the internal template and
            returns the rendered ODF document.
        """

        self.unpack_template()

        # Render content.xml
        self.prepare_template_tags(self.content)
        template = self.environment.from_string(self.content.toxml())
        result = template.render(**kwargs)
        result = result.replace('\n', '<text:line-break/>')

        # Replace original body with rendered body
        original_body = self.content.getElementsByTagName('office:body')[0]
        rendered_body = parseString(result.encode('ascii', 'xmlcharrefreplace')) \
            .getElementsByTagName('office:body')[0]

        document = self.content.getElementsByTagName('office:document-content')[0]
        document.replaceChild(rendered_body, original_body)

        # Render style.xml
        self.prepare_template_tags(self.styles)
        template = self.environment.from_string(self.styles.toxml())
        result = template.render(**kwargs)
        result = result.replace('\n', '<text:line-break/>')
        self.styles = parseString(result.encode('ascii', 'xmlcharrefreplace'))

        self.pack_document()
        return self.rendered.getvalue()


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
        span = xml_document.createElement('text:span')
        text_node = self.create_text_node(xml_document, content)
        span.appendChild(text_node)

        return span

    def create_text_node(self, xml_document, text):
        """
        Creates a text node
        """
        return xml_document.createTextNode(text)


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

                if re.findall(r'\|markdown', field_content):
                    # a markdown should take the whole paragraph
                    field_description = 'text:p'

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


    def get_style_by_name(self, style_name):
        """
            Search in <office:automatic-styles> for style_name.
            Return None if style_name is not found. Otherwise
            return the style node
        """

        auto_styles = self.content.getElementsByTagName('office:automatic-styles')[0]

        if not auto_styles.hasChildNodes():
            return None

        for style_node in auto_styles.childNodes:
            if style_node.hasAttribute('style:name') and \
               (style_node.getAttribute('style:name') == style_name):
               return style_node

        return None

    def insert_style_in_content(self, style_name, attributes=None,
        **style_properties):
        """
            Insert a new style into content.xml's <office:automatic-styles> node.
            Returns a reference to the newly created node
        """

        auto_styles = self.content.getElementsByTagName('office:automatic-styles')[0]
        style_node = self.content.createElement('style:style')

        style_node.setAttribute('style:name', style_name)
        style_node.setAttribute('style:family', 'text')
        style_node.setAttribute('style:parent-style-name', 'Standard')

        if attributes:
            for k, v in attributes.iteritems():
                style_node.setAttribute('style:%s' % k, v)

        if style_properties:
            style_prop = self.content.createElement('style:text-properties')
            for k, v in style_properties.iteritems():
                style_prop.setAttribute('%s' % k, v)

            style_node.appendChild(style_prop)

        return auto_styles.appendChild(style_node)

    def markdown_filter(self, markdown_text):
        """
            Convert a markdown text into a ODT formated text
        """

        if not isinstance(markdown_text, basestring):
            return ''

        from xml.dom import Node
        from markdown_map import transform_map

        try:
            from markdown2 import markdown
        except ImportError:
            raise SecretaryError('Could not import markdown2 library. Install it using "pip install markdown2"')

        styles_cache = {}   # cache styles searching
        html_text = markdown(markdown_text)
        xml_object = parseString('<html>%s</html>' % html_text)

        # Transform HTML tags as specified in transform_map
        # Some tags may require extra attributes in ODT.
        # Additional attributes are indicated in the 'attributes' property

        for tag in transform_map:
            html_nodes = xml_object.getElementsByTagName(tag)
            for html_node in html_nodes:
                odt_node = xml_object.createElement(transform_map[tag]['replace_with'])

                # Transfer child nodes
                if html_node.hasChildNodes():
                    for child_node in html_node.childNodes:
                        odt_node.appendChild(child_node.cloneNode(True))

                # Add style-attributes defined in transform_map
                if 'style_attributes' in transform_map[tag]:
                    for k, v in transform_map[tag]['style_attributes'].iteritems():
                        odt_node.setAttribute('text:%s' % k, v)

                # Add defined attributes
                if 'attributes' in transform_map[tag]:
                    for k, v in transform_map[tag]['attributes'].iteritems():
                        odt_node.setAttribute(k, v)

                    # copy original href attribute in <a> tag
                    if tag == 'a':
                        if html_node.hasAttribute('href'):
                            odt_node.setAttribute('xlink:href',
                                html_node.getAttribute('href'))

                # Does the node need to create an style?
                if 'style' in transform_map[tag]:
                    name = transform_map[tag]['style']['name']
                    if not name in styles_cache:
                        style_node = self.get_style_by_name(name)

                        if style_node is None:
                            # Create and cache the style node
                            style_node = self.insert_style_in_content(
                                name, transform_map[tag]['style'].get('attributes', None),
                                **transform_map[tag]['style']['properties'])
                            styles_cache[name] = style_node

                html_node.parentNode.replaceChild(odt_node, html_node)

        def node_to_string(node):
            result = node.toxml()

            # linebreaks in preformated nodes should be converted to <text:line-break/>
            if (node.__class__.__name__ != 'Text') and \
                (node.getAttribute('text:style-name') == 'Preformatted_20_Text'):
                result = result.replace('\n', '<text:line-break/>')

            # All double linebreak should be replaced with an empty paragraph
            return result.replace('\n\n', '<text:p text:style-name="Standard"/>')


        return ''.join(node_as_str for node_as_str in map(node_to_string,
                xml_object.getElementsByTagName('html')[0].childNodes))

def render_template(template, **kwargs):
    """
        Render a ODF template file
    """

    engine = Render(file)
    return engine.render(**kwargs)


if __name__ == "__main__":
    import os
    from datetime import datetime

    def read(fname):
        return open(os.path.join(os.path.dirname(__file__), fname)).read()

    document = {
        'datetime': datetime.now(),
        'md_sample': read('README.md')
    }

    countries = [
        {'country': 'United States', 'capital': 'Washington', 'cities': ['miami', 'new york', 'california', 'texas', 'atlanta']},
        {'country': 'England', 'capital': 'London', 'cities': ['gales']},
        {'country': 'Japan', 'capital': 'Tokio', 'cities': ['hiroshima', 'nagazaki']},
        {'country': 'Nicaragua', 'capital': 'Managua', 'cities': ['león', 'granada', 'masaya']},
        {'country': 'Argentina', 'capital': 'Buenos aires'},
        {'country': 'Chile', 'capital': 'Santiago'},
        {'country': 'Mexico', 'capital': 'MExico City', 'cities': ['puebla', 'cancun']},
    ]


    render = Render('simple_template.odt')
    result = render.render(countries=countries, document=document)

    output = open('rendered.odt', 'w')
    output.write(result)

    print("Template rendering finished! Check rendered.odt file.")
