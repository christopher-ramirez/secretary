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
import time
import re
import sys
import zipfile
from os import path
from mimetypes import guess_type, guess_extension
from uuid import uuid4
from jinja2 import Environment, Undefined,TemplateSyntaxError,TemplateError
from lxml import etree

try:
    if sys.version_info.major == 3:
        xrange = range
        basestring = (str, bytes)
except AttributeError:
    # On Python 2.6 sys.version_info is a tuple
    if not isinstance(sys.version_info, tuple):
        raise

nodes_added_vars={}

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

def media_loader(f):
    def wrapper(*args, **kwargs):
        Renderer.__media_loader__ = f

    return wrapper

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

        print('Initing a Renderer instance\nTemplate')

        if environment:
            self.environment = environment
        else:
            self.environment = Environment(undefined=UndefinedSilently,
                                           autoescape=True)
            # Register filters
            self.environment.filters['pad'] = pad_string
            self.environment.filters['markdown'] = self.markdown_filter
            self.environment.filters['image'] = self.image_filter

        self.media_path = kwargs.pop('media_path', '')
        self.media_callback = self.fs_loader


    def media_loader(self, callback):
        ms_start = time.time()*1000.0
        """This sets the the media loader. A user defined function which
        loads media. The function should take a template value, optionals
        args and kwargs. Is media exists should return a tuple whose first
        element if a file object type representing the media and its second
        elements is the media mimetype.

        See Renderer.fs_loader funcion for an example"""
        self.media_callback = callback
        ms_end = time.time()*1000.0
        print('Tempo loader:'+str(ms_end - ms_start))
        return callback

    def _unpack_template(self, template):
        ms_start = time.time()*1000.0
        # And Open/libreOffice is just a ZIP file. Here we unarchive the file
        # and return a dict with every file in the archive
        print('Unpacking template file')
        
        archive_files = {}
        archive = zipfile.ZipFile(template, 'r')
        for zfile in archive.filelist:
            archive_files[zfile.filename] = archive.read(zfile.filename)

        ms_end = time.time()*1000.0
        print('Tempo unpack:'+str(ms_end - ms_start))
        return archive_files

        print('Unpack completed')

    def _pack_document(self, files):
        # Store to a zip files in files
        ms_start = time.time()*1000.0

        print('packing document')
        zip_file = io.BytesIO()

        zipdoc = zipfile.ZipFile(zip_file, 'a')
        for fname, content in files.items():
            if sys.version_info >= (2, 7):
                zipdoc.writestr(fname, content, zipfile.ZIP_DEFLATED)
            else:
                zipdoc.writestr(fname, content)

        print('Document packing completed')
        ms_end = time.time()*1000.0
        print('Tempo pack:'+str(ms_end - ms_start))

        return zip_file

    def _prepare_template_tags(self, xml_document):
        """ Here we search for every field node present in xml_document.
        For each field we found we do:
        * if field is a print field ({{ field }}), we replace it with a
          <text:span> node.
        
        * if field is a control flow ({% %}), then we find immediate node of
          type indicated in field's `text:description` attribute and replace
          the whole node and its childrens with field's content.
        
          If `text:description` attribute starts with `before::` or `after::`,
          then we move field content before or after the node in description.
        
          If no `text:description` is available, find the immediate common
          parent of this and any other field and replace its child and 
          original parent of field with the field content.
        
          e.g.: original
          <table>
              <table:row>
                  <field>{% for bar in bars %}</field>
              </table:row>
              <paragraph>
                  <field>{{ bar }}</field>
              </paragraph>
              <table:row>
                  <field>{% endfor %}</field>
              </table:row>
          </table>
          
          After processing:
          <table>
              {% for bar in bars %}
              <paragraph>
                  <text:span>{{ bar }}</text:span>
              </paragraph>
              {% endfor %}
          </table>
        """

        print('Preparing template tags')
        fields = self.retrieve_nodes_by_name(xml_document,'{urn:oasis:names:tc:opendocument:xmlns:text:1.0}text-input')

        # First, count secretary fields
        for field in fields:

            field_content = field.text.strip()

            if not re.findall(r'(?is)^{[{|%].*[%|}]}$', field_content):
                # Field does not contains jinja template tags
                continue

            is_block_tag = re.findall(r'(?is)^{%[^{}]*%}$', field_content)
            pn = field.getparent()
            self.inc_node_fields_count(pn,'block' if is_block_tag else 'variable')

        # Do field replacement and moving
        for field in fields:

            bt = False
            of = False

            field_content = field.text.strip()

            if not re.findall(r'(?is)^{[{|%].*[%|}]}$', field_content):
                # Field does not contains jinja template tags
                continue

            is_block_tag = re.findall(r'(?is)^{%[^{}]*%}$', field_content)
            discard = field
            field_reference = field.get('{urn:oasis:names:tc:opendocument:xmlns:text:1.0}description').strip().lower()

            if re.findall(r'\|markdown', field_content):
                # a markdown field should take the whole paragraph
                field_reference = 'text:p'

            if field_reference:
                # User especified a reference. Replace immediate parent node
                # of type indicated in reference with this field's content.
                node_type = FLOW_REFERENCES.get(field_reference, False)
                if node_type:
                    discard = self._parent_of_type(field, node_type)
            elif is_block_tag:
                # Find the common immediate parent of this and any other field.

                while nodes_added_vars[discard.getparent()]['secretary_field_count'] <= 1:
                    discard = discard.getparent()

                if discard is not None:
                    bt = True
            else:
                ot=True
                jinja_node = self.create_text_span_node_new(xml_document,
                                                            field_content)

            parent = discard.getparent()
            if not field_reference.startswith('after::'):
                if bt:
                    discard.getprevious().tail = field_content
                elif ot:
                    discard.addprevious(jinja_node)
            else:
                children = parent.getchildren
                if children is not None:
                    childrensize = len(parent)
                    parentlastchild =  children[childrensize]

                if discard == parentlastchild:
                    if bt:
                        discard.getprevious().tail = field_content
                    elif ot:
                        discard.addprevious(jinja_node)
                else:
                    if bt:
                        discard.getprevious().tail = field_content
                    elif ot:
                        parent.addprevious(jinja_node,discard.getnext)

            if field_reference.startswith(('after::', 'before::')):
                # Do not remove whole field container. Just remove the
                # <text:text-input> parent node if field has it.
                discard = self._parent_of_type(field, 'text:p')
                parent = discard.getparent()

            parent.remove(discard)

    def issamenode(nodeaa,nodeb,tagsame=True):
        for attrib in nodeaa.attrib:
            if nodeaa.get(attrib) != nodeb.get(attrib):
                #print (nodeaa.get(attrib),nodeb.get(attrib))
                return False
            else:
                return False
        if nodeaa.text != nodeb.text:
            return False
        if tagsame==True:
            if nodeaa.tag != nodeb.tag:
                return False
        if nodeaa.prefix != nodeb.prefix:
            return False
        if nodeaa.tail != nodeb.tail:
            return False
        if nodeaa.values()!=nodeb.values(): #may be redundant to the attrib matching
            return False
        if nodeaa.keys() != nodeb.keys(): #may also be redundant to the attrib matching
            return False
        return True

    @staticmethod
    def _unescape_entities(xml_text):
        """
        Strips tags of the form <text:span ...> from inside Jinja elements
        and unescapes HTML codes for >, <, & and "
        """
        unescape_rules = {
            r'(?is)({([{%])[^%}]*?)(</?text:s.*?>)(.*?[%}]})': r'\1 \4',
            r'(?is)({([{%])[^%}]*?)(&gt;)(.*?[%}]})'         : r'\1>\4',
            r'(?is)({([{%])[^%}]*?)(&lt;)(.*?[%}]})'         : r'\1<\4',
            r'(?is)({([{%])[^%}]*?)(&amp;)(.*?[%}]})'        : r'\1&\4',
            r'(?is)({([{%])[^%}]*?)(&quot;)(.*?[%}]})'       : r'\1"\4',
        }

        for regexp, replacement in unescape_rules.items():
            subs_made = True
            while subs_made:
                xml_text, subs_made = re.subn(regexp, replacement, xml_text)

        return xml_text

    @staticmethod
    def _encode_escape_chars(xml_text):
        # Replace line feed and/or tabs within text span entities.
        find_pattern = r'(?is)<text:([\S]+?)>([^>]*?([\n|\t])[^<]*?)</text:\1>'
        for m in re.findall(find_pattern, xml_text):
            replacement = m[1].replace('\n', '<text:line-break/>')
            replacement = replacement.replace('\t', '<text:tab/>')
            xml_text = xml_text.replace(m[1], replacement)

        return xml_text

    def add_media_to_archive(self, media, mime, name=''):
        """Adds to "Pictures" archive folder the file in `media` and register
        it into manifest file."""
        extension = None
        if hasattr(media, 'name') and not name:
            extension = path.splitext(media.name)
            name      = extension[0]
            extension = extension[1]

        if not extension:
            extension = guess_extension(mime)

        media_path = 'Pictures/%s%s' % (name, extension)
        media.seek(0)
        self.files[media_path] = media.read(-1)
        if hasattr(media, 'close'):
            media.close()

        files_node = self.manifest.getroot()
        node = self.create_node(self.manifest, '{urn:oasis:names:tc:opendocument:xmlns:manifest:1.0}file-entry', files_node)
        node.set('{urn:oasis:names:tc:opendocument:xmlns:manifest:1.0}full-path', media_path)
        node.set('{urn:oasis:names:tc:opendocument:xmlns:manifest:1.0}media-type', mime)

        return media_path

    def fs_loader(self, media, *args, **kwargs):
        """Loads a file from the file system.
        :param media: A file object or a relative or absolute path of a file.
        :type media: unicode
        """
        if hasattr(media, 'seek') and hasattr(media, 'read'):
            return (media, 'image/jpeg')
        elif path.isfile(media):
            filename = media
        else:
            if not self.media_path:
                print('media_path property not specified to load images from.')
                return

            filename = path.join(self.media_path, media)
            if not path.isfile(filename):
                print('Media file "%s" does not exists.' % filename)
                return

        mime = guess_type(filename)
        return (open(filename, 'rb'), mime[0] if mime else None)

    def replace_images(self, xml_document):
        """Perform images replacements"""
        print('Inserting images')
        frames = self.retrieve_nodes_by_name(xml_document,str('{urn:oasis:names:tc:opendocument:xmlns:drawing:1.0}frame'))

        for frame in frames:

            if not len(frame):
                continue

            key = frame.get('{urn:oasis:names:tc:opendocument:xmlns:drawing:1.0}name')
            if key not in self.template_images:
                continue

            # Get frame attributes
            frame_attrs = dict()

            for k, v in frame.attrib.iteritems():
                frame_attrs[k] = v
            # Get child draw:image node and its attrs
            image_node = frame[0]
            image_attrs = dict()

            for k, v in image_node.attrib.iteritems():
                image_attrs[k] = v

            # Request to media loader the image to use
            image = self.media_callback(self.template_images[key]['value'],
                                        *self.template_images[key]['args'],
                                        frame_attrs=frame_attrs,
                                        image_attrs=image_attrs,
                                        **self.template_images[key]['kwargs'])

            # Update frame and image node attrs (if they where updated in
            # media_callback call)
            for k, v in frame_attrs.items():
                frame.set(k, v)
                
            for k, v in image_attrs.items():
                image_node.set(k, v)

            # Keep original image reference value
            if isinstance(self.template_images[key]['value'], basestring):
                frame.set('{urn:oasis:names:tc:opendocument:xmlns:drawing:1.0}name',self.template_images[key]['value'])

            # Does the madia loader returned something?
            if not image:
                continue

            mname = self.add_media_to_archive(media=image[0], mime=image[1],name=key)
            if mname:
                image_node.set('{http://www.w3.org/1999/xlink}href', mname)

    def _render_xml(self, xml_document, **kwargs):
        # Prepare the xml object to be processed by jinja2
        ms_start = time.time()*1000.0

        print('Rendering XML object')

        template_string = ""

        try:
            self.template_images = dict()
            self._prepare_template_tags(xml_document)

            template_string = self._unescape_entities(etree.tostring(xml_document,encoding='unicode',pretty_print=True))
            jinja_template = self.environment.from_string(template_string)

            result = jinja_template.render(**kwargs)
            result = self._encode_escape_chars(result)

            #final_xml  =  etree.parse(result)
            final_xml  =  etree.fromstring(result)

            if self.template_images:
                self.replace_images(final_xml)

            return final_xml
        except TemplateSyntaxError, inst:
            self.log.error('Error rendering template:\n%s',
                           xml_document, exc_info=True)
            self.log.error('Unescaped template line:'+str(inst.lineno))
            raise
        except TemplateError :
            self.log.error('Error rendering template:\n%s',
                           xml_document, exc_info=True)

            raise
        except:
            self.log.error('Error rendering template:\n%s',
                           xml_document, exc_info=True)

            raise
        finally:
            ms_end = time.time()*1000.0
            print('Tempo _render_xml:'+str(ms_end - ms_start))
            print('Rendering xml object finished')

    def retrieve_nodes_by_name(self,rootelement,tagnodename):

        nodes=[]

        for rootiter in rootelement.getiterator():
            for node in rootiter:
                #print(node)
                tag_text = str(node.tag)
                if tag_text == tagnodename:
                    #print("tag:"+str(node.tag))
                    #print("text:"+str(node.text))
                    nodes.append(node)

        return nodes

    def render(self, template, use_parallel_xml_render='False',parallel_xml_render_max_workers=5,**kwargs):
        ms_start = time.time()*1000.0

        """
            Render a template

            args:
                template: A template file. Could be a string or a file instance
                **kwargs: Template variables. Similar to jinja2

            returns:
                A binary stream which contains the rendered document.
        """

        print('Initing a template rendering')
        self.files = self._unpack_template(template)
        self.render_vars = {}


        # Keep content and styles object since many functions or
        # filters may work with then

        ms_start_t = time.time()*1000.0
        ms_start = time.time()*1000.0
        contentobject = io.BytesIO(self.files['content.xml'])
        self.content  =  etree.parse(contentobject)
        ms_end = time.time()*1000.0
        print('Tempo parse content.xml1 lxml:'+(str(ms_end-ms_start)))

        ms_start = time.time()*1000.0
        stylesobject = io.BytesIO(self.files['styles.xml'])
        self.styles  = etree.parse(stylesobject)
        ms_end = time.time()*1000.0
        print('Tempo parse styles.xml lxml:'+(str(ms_end-ms_start)))

        ms_start = time.time()*1000.0
        manifestobject = io.BytesIO(self.files['META-INF/manifest.xml'])
        self.manifest = etree.parse(manifestobject)
        ms_end = time.time()*1000.0
        print('Tempo parse manifest.xml lxml:'+(str(ms_end-ms_start)))

        ms_end_t = time.time()*1000.0
        print('Tempo totale parse lxml:'+(str(ms_end_t-ms_start_t)))

        ms_end = time.time()*1000.0
        print('Tempo parse manifest.xml lxml:'+(str(ms_end-ms_start)))

        # Render content.xml keeping just 'office:body' node.

        print('use_parallel_xml_render:'+use_parallel_xml_render)

        ms_start = time.time()*1000.0
        try:
            self.styles = self._render_xml(self.styles, **kwargs)
            rendered_content = self._render_xml(self.content, **kwargs)
        except Exception,inst:
            raise
        finally:
            ms_end = time.time()*1000.0

        print('Tempo totale render xml content e style:'+(str(ms_end-ms_start)))

        original_node = self.content.getroot().find('{urn:oasis:names:tc:opendocument:xmlns:office:1.0}body')
        new_node =  rendered_content.find('{urn:oasis:names:tc:opendocument:xmlns:office:1.0}body')
        self.content.getroot().replace(original_node,new_node)


        print('Template rendering finished')

        self.files['content.xml']           = etree.tostring(self.content).encode('ascii', 'xmlcharrefreplace')
        self.files['styles.xml']           = etree.tostring(self.styles).encode('ascii', 'xmlcharrefreplace')
        self.files['META-INF/manifest.xml']  = etree.tostring(self.manifest).encode('ascii', 'xmlcharrefreplace')

        document = self._pack_document(self.files)
        ms_end = time.time()*1000.0
        print('Tempo render:'+str(ms_end - ms_start))
        return document.getvalue()

    def renderxml(self,xml,**kwargs):
        print('renderxml')
        try:
            return self._render_xml(xml, **kwargs)
        except:
            raise


    """
    def parsexml(self,xml):
        print('parse xml')
        xmlobject = io.BytesIO(xml)
        output  = etree.parse(xmlobject)
        return output

    def parsexmls(self):

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        futures = {}
        ms_start = time.time()*1000.0

        tpstyles = executor.submit(self.parsexml, self.files['styles.xml'])
        tpcontent = executor.submit(self.parsexml, self.files['content.xml'])
        tpmanifest = executor.submit(self.parsexml, self.files['META-INF/manifest.xml'])

        futures[tpstyles] = 'tpstyles'
        futures[tpcontent] = 'tpcontent'
        futures[tpmanifest] = 'tpmanifest'

        result = concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.ALL_COMPLETED)
        ms_end = time.time()*1000.0
        print('Tempo totale parse xmls:'+(str(ms_end-ms_start)))


        self.styles = tpstyles.result()
        self.content = tpcontent.result()
        self.manifest = tpmanifest.result()
    """


    def _parent_of_type(self, node, of_type):
        # Returns the first immediate parent of type `of_type`.
        # Returns None if nothing is found.

        if hasattr(node, 'parentNode'):
            if node.getparent.name.lower() == of_type:
                return node.getparent
            else:
                pn = node.getparent
                return self._parent_of_type(pn, of_type)
        else:
            return None

    def create_node(self, xml_document, node_type, parent=None):
        """Creates a node in `xml_document` of type `node_type` and specified,
        as child of `parent`."""
        node = etree.SubElement(parent, node_type)
        """
        node = xml_document.createElement(node_type)
        if parent:
            parent.appendChild(node)
        """
        return node

    def create_text_span_node_new(self, xml_document, content):
        span = etree.Element('{urn:oasis:names:tc:opendocument:xmlns:text:1.0}span')
        span.text = content
        return span

    def create_text_node(self, xml_document, text):
        return None

    def inc_node_fields_count(self, node, field_type='variable'):
        """ Increase field count of node and its parents """

        if node is None:
            return

        try:
            if nodes_added_vars[node] is None:
                node_external_vars = {}
                nodes_added_vars[node] = node_external_vars
        except:
            node_external_vars = {}
            nodes_added_vars[node] = node_external_vars

        node_external_vars = nodes_added_vars[node]

        try:
            if node_external_vars[str('secretary_field_count')] is None:
                node_external_vars[str('secretary_field_count')] = 0
        except:
            node_external_vars[str('secretary_field_count')] = 0

        try:
            if node_external_vars[str('secretary_variable_count')] is None:
                node_external_vars[str('secretary_variable_count')] = 0
        except:
            node_external_vars[str('secretary_variable_count')] = 0

        try:
            if node_external_vars[str('secretary_block_count')] is None:
                node_external_vars[str('secretary_block_count')] = 0
        except:
            node_external_vars[str('secretary_block_count')] = 0

        node_external_vars[str('secretary_field_count')] += 1

        #node.secretary_field_count += 1
        if field_type == 'variable':
            node_external_vars[str('secretary_variable_count')] += 1
            #node.secretary_variable_count += 1
        else:
            node_external_vars[str('secretary_block_count')] += 1
            #node.secretary_block_count += 1
        pn = node.getparent()
        self.inc_node_fields_count(pn, field_type)

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

    def image_filter(self, value, *args, **kwargs):
        """Store value into template_images and return the key name where this
        method stored it. The value returned it later used to load the image
        from media loader and finally inserted into the final ODT document."""
        key = uuid4().hex
        self.template_images[key] = {
            'value': value,
            'args': args,
            'kwargs': kwargs
        }

        return key


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
