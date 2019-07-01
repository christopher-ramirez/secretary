'''
    secretary.renderers module

    Contains classes implementing rendering XML based documents
'''

import re
import sys
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError
from jinja2 import Markup


PY2 = sys.version_info < (3, 0)

if PY2:
    from urllib import unquote
else:
    from urllib.parse import unquote


class JinjaTagsUtils(object):
    '''
    A class used as an interface for scaping and working with jinja tags.
    '''
    def __init__(self, environment):
        self.environment = environment
        self._compile_tags()
        self._compile_escape_expressions()

        for attr in ['variable_start_string', 'variable_end_string',
                     'block_start_string', 'block_end_string']:
            setattr(self, attr, getattr(environment, attr, ''))

    def _compile_tags(self):
        self.tag_pattern = re.compile(r'(?is)^({0}|{1}).*({2}|{3})$'.format(
            self.environment.variable_start_string,
            self.environment.block_start_string,
            self.environment.variable_end_string,
            self.environment.block_end_string
        ))

        self.variable_pattern = re.compile(r'(?is)({0})(.*)({1})$'.format(
            self.environment.variable_start_string,
            self.environment.variable_end_string
        ))

        self.block_pattern = re.compile(r'(?is)^{0}.*{1}$'.format(
            self.environment.block_start_string,
            self.environment.block_end_string
        ))

    def _compile_escape_expressions(self):
        self.escape_map = dict()
        unescape_rules = {
            r'&gt;': r'>',
            r'&lt;': r'<',
            r'&amp;': r'&',
            r'&quot;': r'"',
            r'&apos;': r"'",
        }

        for key, value in unescape_rules.items():
            exp = r'(?is)(({0}|{1})[^{3}{4}]*?)({2})([^{0}{1}]*?({3}|{4}))'
            key = re.compile(exp.format(
                self.environment.variable_start_string,
                self.environment.block_start_string,
                key,
                self.environment.variable_end_string,
                self.environment.block_end_string
            ))

            self.escape_map[key] = r'\1{0}\4'.format(value)

    def is_tag(self, tag):
        '''
        Returns True if tag is a valid jinja instruction tag.
        '''
        return len(self.tag_pattern.findall(tag)) > 0

    def is_block_tag(self, tag):
        '''
        Returns True is tag is a jinja flow control tag.
        '''
        return len(self.block_pattern.findall(tag)) > 0

    def unescape_entities(self, xml_text):
        '''
        Unescape links and '&amp;', '&lt;', '&quot;' and '&gt;' within jinja
        instructions. The regexs rules used here are compiled in
        _compile_escape_expressions.
        '''
        for regexp, replacement in self.escape_map.items():
            while True:
                xml_text, substitutions = regexp.subn(replacement, xml_text)
                if not substitutions:
                    break

        return self._unescape_links(xml_text)

    def _unescape_links(self, xml_text):
        '''
        Fix Libreoffice auto escaping of xlink:href attribute values.
        This unescaping is only done on 'secretary' scheme URLs.
        '''
        robj = re.compile(r'(?is)(xlink:href=\")secretary:(.*?)(\")')

        def replacement(match):
            return Markup(''.join([
                match.group(1),
                self.variable_pattern.sub(r'\1 SafeValue(\2) \3',
                                          unquote(match.group(2))),
                match.group(3)
            ]))

        while True:
            xml_text, rep = robj.subn(replacement, xml_text)
            if not rep:
                break

        return xml_text


class RenderJob(object):
    '''
    RenderJob class. We call "job" the process of transforming a ODT template
    into a final ODT document with all its ligic processed and variables replaced.

    It's a job because it can be a multi step process. An *.odt document file
    may need to render more than one different XML file.

    Classes that inherit from RenderJob must implement render() interface.
    This function is responsible for rendering the template into a final doc.

    Inherited classes must also implement RenderJob.dd_document_media().
    The function is responsible for adding a media file to the final document.
    '''

    def __init__(self, renderer, template, **variables):
        self.files = {}
        self.work_variables = {}
        self.renderer = renderer
        self.template = template
        self.variables = variables

    def render(self):
        '''
        Renders this job's template and returns a final document from it.
        '''
        raise NotImplementedError

    def add_document_media(self, reference_node, media, **kwargs):
        '''
        Adds a media to current document.
        '''
        raise NotImplementedError

    def _before_job_start(self):
        self.renderer.notify_job_start(self)

    def _after_job_end(self):
        self.renderer.notify_job_end(self)

    def render_xml(self, xml):
        '''
        Render an ODT XML document. A Job may call this function multiple
        times. Depending of the number of XMLs that are part of the document.
        '''
        from .xmlrender import XMLRender
        xml = parseString(xml)
        self._before_render_xml(xml)
        render_job = XMLRender(self, xml)
        rendered_xml_string = render_job.render(**self.variables)

        try:
            final_xml = parseString(rendered_xml_string.encode('utf-8'))
            self._after_render_xml(final_xml)
        except ExpatError as e:
            N_CONTEXT_CHARS = 38
            line = rendered_xml_string.split('\n')[e.lineno - 1]
            lower = max(0, e.offset - N_CONTEXT_CHARS)
            upper = min(e.offset + N_CONTEXT_CHARS, len(line))
            context = line[lower:upper]
            e.args = ('Invalid XML near line {}, column {}\n{}\n{}'.format(
                e.lineno, e.offset, context, '-' * (e.offset - lower) + '^'),)
            raise

        return final_xml.toxml().encode('utf-8')

    def _before_render_xml(self, xml):
        self.renderer.notify_xml_render_start(self, xml)

    def _after_render_xml(self, xml):
        self.renderer.notify_xml_render_end(self, xml)
