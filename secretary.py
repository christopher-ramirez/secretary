#!/usr/bin/python

# * Copyright (c) 2012-2014 Christopher Ramirez chris.ramirezg@gmail.com
# *
# * Licensed under the MIT license.

"""
Secretary
    This project is a document engine which make use of LibreOffice
    documents as templates and use the semantics of jinja2 to control
    variable printing and control flow.

    To render a template:
        engine = Renderer(template_file)
        result = engine.render(template_var1=...)
"""

from __future__ import unicode_literals, print_function

import io
import re
import sys
import logging
import zipfile
from xml.dom.minidom import parseString
from jinja2 import Environment, Undefined

# Test python versions and normalize calls to basestring, unicode, etc.
try:
    unicode = unicode
except NameError:
    # 'unicode' is undefined, must be Python 3
    str = str
    unicode = str
    bytes = bytes
    basestring = (str,bytes)
else:
    # 'unicode' exists, must be Python 2
    str = str
    unicode = unicode
    bytes = str
    basestring = basestring


FLOW_REFERENCES = {
    'text:p'             : 'text:p',
    'paragraph'          : 'text:p',
    'before::paragraph'  : 'text:p',
    'after::paragraph'   : 'text:p',

    'table:table-row'    : 'table:table-row',
    'table-row'          : 'table:table-row',
    'row'                : 'table:table-row',
    'before::table-row'  : 'table:table-row',
    'after::table-row'   : 'table:table-row',
    'before::row'        : 'table:table-row',
    'after::row'         : 'table:table-row',

    'table:table-cell'   : 'table:table-cell',
    'table-cell'         : 'table:table-cell',
    'cell'               : 'table:table-cell',
    'before::table-cell' : 'table:table-cell',
    'after::table-cell'  : 'table:table-cell',
    'before::cell'       : 'table:table-cell',
    'after::cell'        : 'table:table-cell',
}

# ---- Exceptions
class SecretaryError(Exception):
    pass

class UndefinedSilently(Undefined):
    # Silently undefined,
    # see http://stackoverflow.com/questions/6182498
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


class Renderer(object):
    """
        Main engine to convert and ODT document into a jinja
        compatible template.

        Basic use example:
            engine = Renderer('template')
            result = engine.render()


        Renderer provides an enviroment variable which can be used
        to provide custom filters to the ODF render.

            engine = Renderer('template.odt')
            engine.environment.filters['custom_filer'] = filter_function
            result = engine.render()
    """


    def __init__(self, environment=None, **kwargs):
        """
        Create a Renderer instance.

        args:
            environment: Use this jinja2 enviroment. If not specified, we
                         create a new environment for this class instance.

        returns:
            None
        """
        self.log = logging.getLogger(__name__)
        self.log.debug('Initing a Renderer instance\nTemplate')

        if environment:
            self.environment = environment
        else:
            self.environment = Environment(undefined=UndefinedSilently,
                                           autoescape=True)
            # Register filters
            self.environment.filters['pad'] = pad_string
            self.environment.filters['markdown'] = self.markdown_filter

    def _unpack_template(self, template):
        # And Open/libreOffice is just a ZIP file. Here we unarchive the file
        # and return a dict with every file in the archive
        self.log.debug('Unpacking template file')
        
        archive_files = {}
        archive = zipfile.ZipFile(template, 'r')
        for zfile in archive.filelist:
            archive_files[zfile.filename] = archive.read(zfile.filename)

        return archive_files

        self.log.debug('Unpack completed')


    def _pack_document(self, files):
        # Store to a zip files in files
        self.log.debug('packing document')
        zip_file = io.BytesIO()

        zipdoc = zipfile.ZipFile(zip_file, 'a')
        for fname, content in files.items():
            if sys.version_info >= (2, 7):
                zipdoc.writestr(fname, content, zipfile.ZIP_DEFLATED)
            else:
                zipdoc.writestr(fname, content)

        self.log.debug('Document packing completed')

        return zip_file

    def _prepare_template_tags(self, xml_document):
        # Here we search for every field node present in xml_document.
        # For each field we found we do:
        # * if field is a print field ({{ field }}), we replace it with a
        #   <text:span> node.
        # 
        # * if field is a control flow ({% %}), then we find immediate node of
        #   type indicated in field's `text:description` attribute and replace
        #   the whole node and its childrens with field's content.
        # 
        #   If `text:description` attribute starts with `before::` or `after::`,
        #   then we move field content before or after the node in description.
        # 
        #   If no `text:description` is available, find the immediate common
        #   parent of this and any other field and replace its child and 
        #   original parent of field with the field content.
        # 
        #   e.g.: original
        #   <table>
        #       <table:row>
        #           <field>{% for bar in bars %}</field>
        #       </table:row>
        #       <paragraph>
        #           <field>{{ bar }}</field>
        #       </paragraph>
        #       <table:row>
        #           <field>{% endfor %}</field>
        #       </table:row>
        #   </table>
        #   
        #   After processing:
        #   <table>
        #       {% for bar in bars %}
        #       <paragraph>
        #           <text:span>{{ bar }}</text:span>
        #       </paragraph>
        #       {% endfor %}
        #   </table>

        self.log.debug('Preparing template tags')
        fields = xml_document.getElementsByTagName('text:text-input')

        # First, count secretary fields
        for field in fields:
            if not field.hasChildNodes():
                continue

            field_content = field.childNodes[0].data.strip()

            if not re.findall(r'(?is)^{[{|%].*[%|}]}$', field_content):
                # Field does not contains jinja template tags
                continue

            is_block_tag = re.findall(r'(?is)^{%[^{}]*%}$', field_content)
            self.inc_node_fields_count(field.parentNode,
                    'block' if is_block_tag else 'variable')

        # Do field replacement and moving
        for field in fields:
            if not field.hasChildNodes():
                continue

            field_content = field.childNodes[0].data.strip()

            if not re.findall(r'(?is)^{[{|%].*[%|}]}$', field_content):
                # Field does not contains jinja template tags
                continue

            is_block_tag = re.findall(r'(?is)^{%[^{}]*%}$', field_content)
            discard = field
            field_reference = field.getAttribute('text:description').strip().lower()

            if re.findall(r'\|markdown', field_content):
                # a markdown field should take the whole paragraph
                field_reference = 'text:p'

            if field_reference:
                # User especified a reference. Replace immediate parent node
                # of type indicated in reference with this field's content.
                node_type = FLOW_REFERENCES.get(field_reference, False)
                if node_type:
                    discard = self._parent_of_type(field, node_type)

                jinja_node = self.create_text_node(xml_document, field_content)

            elif is_block_tag:
                # Find the common immediate parent of this and any other field.
                while discard.parentNode.secretary_field_count <= 1:
                    discard = discard.parentNode

                if discard is not None:
                    jinja_node = self.create_text_node(xml_document,
                                                       field_content)

            else:
                jinja_node = self.create_text_span_node(xml_document,
                                                        field_content)

            parent = discard.parentNode
            if not field_reference.startswith('after::'):
                parent.insertBefore(jinja_node, discard)
            else:
                if discard.isSameNode(parent.lastChild):
                    parent.appendChild(jinja_node)
                else:
                    parent.insertBefore(jinja_node,
                                        discard.nextSibling)

            if field_reference.startswith(('after::', 'before::')):
                # Do not remove whole field container. Just remove the
                # <text:text-input> parent node if field has it.
                discard = self._parent_of_type(field, 'text:p')
                parent = discard.parentNode

            parent.removeChild(discard)


    def _unescape_entities(self, xml_text):
        # unescape XML entities gt and lt
        unescape_rules = {
            r'(?is)({[{|%].*)(&gt;)(.*[%|}]})': r'\1>\3',
            r'(?is)({[{|%].*)(&lt;)(.*[%|}]})': r'\1<\3',
            r'(?is)({[{|%].*)(<.?text:s.?>)(.*[%|}]})': r'\1 \3',
        }

        for p, r in unescape_rules.items():
            xml_text = re.sub(p, r, xml_text)

        return xml_text

    def _encode_escape_chars(self, xml_text):
        # Replace line feed and/or tabs within text span entities.
        find_pattern = r'(?is)<text:([\S]+?)>([^>]*?([\n|\t])[^<]*?)</text:\1>'
        for m in re.findall(find_pattern, xml_text):
            print(m[1])
            replacement = m[1].replace('\n', '<text:line-break/>')
            replacement = replacement.replace('\t', '<text:tab/>')
            xml_text = xml_text.replace(m[1], replacement)

        return xml_text
        

    def _render_xml(self, xml_document, **kwargs):
        # Prepare the xml object to be processed by jinja2
        self.log.debug('Rendering XML object')

        try:
            self._prepare_template_tags(xml_document)
            template_string = self._unescape_entities(xml_document.toxml())
            jinja_template = self.environment.from_string(template_string)
            result = jinja_template.render(**kwargs)
            result = self._encode_escape_chars(result)

            try:
                return parseString(result.encode('ascii', 'xmlcharrefreplace'))
            except:
                self.log.error('Error parsing XML result:\n%s', result,
                               exc_info=True)
                raise
        
        except:
            self.log.error('Error rendering template:\n%s',
                           xml_document.toprettyxml(), exc_info=True)
            raise
        finally:
            self.log.debug('Rendering xml object finished')


    def render(self, template, **kwargs):
        """
            Render a template

            args:
                template: A template file. Could be a string or a file instance
                **kwargs: Template variables. Similar to jinja2

            returns:
                A binary stream which contains the rendered document.
        """

        self.log.debug('Initing a template rendering')
        self.files = self._unpack_template(template)

        # Keep content and styles object since many functions or
        # filters may work with then
        self.content = parseString(self.files['content.xml']) 
        self.styles = parseString(self.files['styles.xml'])
        
        # Render content.xml
        self.content = self._render_xml(self.content, **kwargs)

        # Render styles.xml
        self.styles = self._render_xml(self.styles, **kwargs)

        self.log.debug('Template rendering finished')

        self.files['content.xml'] = self.content.toxml().encode('ascii', 'xmlcharrefreplace')
        self.files['styles.xml'] = self.styles.toxml().encode('ascii', 'xmlcharrefreplace')
        document = self._pack_document(self.files)
        return document.getvalue()


    def _parent_of_type(self, node, of_type):
        # Returns the first immediate parent of type `of_type`.
        # Returns None if nothing is found.

        if hasattr(node, 'parentNode'):
            if node.parentNode.nodeName.lower() == of_type:
                return node.parentNode
            else:
                return self._parent_of_type(node.parentNode, of_type)
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

    def inc_node_fields_count(self, node, field_type='variable'):
        """ Increase field count of node and its parents """

        if node is None:
            return

        if not hasattr(node, 'secretary_field_count'):
            setattr(node, 'secretary_field_count', 0)

        if not hasattr(node, 'secretary_variable_count'):
            setattr(node, 'secretary_variable_count', 0)

        if not hasattr(node, 'secretary_block_count'):
            setattr(node, 'secretary_block_count', 0)

        node.secretary_field_count += 1
        if field_type == 'variable':
            node.secretary_variable_count += 1
        else:
            node.secretary_block_count += 1

        self.inc_node_fields_count(node.parentNode, field_type)

    
    def get_style_by_name(self, style_name):
        """
            Search in <office:automatic-styles> for style_name.
            Return None if style_name is not found. Otherwise
            return the style node
        """

        auto_styles = self.content.getElementsByTagName(
            'office:automatic-styles')[0]

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
            for k, v in attributes.items():
                style_node.setAttribute('style:%s' % k, v)

        if style_properties:
            style_prop = self.content.createElement('style:text-properties')
            for k, v in style_properties.items():
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
        xml_object = parseString('<html>%s</html>' % html_text.encode('ascii', 'xmlcharrefreplace'))

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
                    for k, v in transform_map[tag]['style_attributes'].items():
                        odt_node.setAttribute('text:%s' % k, v)

                # Add defined attributes
                if 'attributes' in transform_map[tag]:
                    for k, v in transform_map[tag]['attributes'].items():
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

    engine = Renderer(file)
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
        {'country': 'Nicaragua', 'capital': 'Managua', 'cities': ['leon', 'granada', 'masaya']},
        {'country': 'Argentina', 'capital': 'Buenos aires'},
        {'country': 'Chile', 'capital': 'Santiago'},
        {'country': 'Mexico', 'capital': 'MExico City', 'cities': ['puebla', 'cancun']},
    ]

    render = Renderer()
    result = render.render('simple_template.odt', countries=countries, document=document)

    output = open('rendered.odt', 'wb')
    output.write(result)

    print("Template rendering finished! Check rendered.odt file.")
