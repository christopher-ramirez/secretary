import io
import re
import sys
import logging
from os import path
from mimetypes import guess_type, guess_extension
from xmlrender import XMLRender
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError, ErrorString

class Job(object):
    def __init__(self, renderer, template, **variables):
        self.files = {}
        self.work_variables = {}
        self.renderer = renderer
        self.template = template
        self.variables = variables

    def _before_job_start(self):
        self.renderer.notify_job_start(self)

    def _after_job_end(self):
        self.renderer.notify_job_end(self)

    def render_xml(self, xml):
        xml = parseString(xml)
        self._before_render_xml(xml)
        render_job = XMLRender(self, xml)
        rendered_xml_string = render_job.render(**self.variables)

        try:
            final_xml = parseString(rendered_xml_string.encode('utf-8'))
            self._after_render_xml(final_xml)
        except ExpatError as e:
            raise e

        return final_xml.toxml().encode('ascii', 'xmlcharrefreplace')

    def add_document_media(self, reference_node, media, **kwargs):
        """Adds a media to current document."""
        raise NotImplementedError

    def _before_render_xml(self, xml):
        self.renderer.notify_xml_render_start(self, xml)

    def _after_render_xml(self, xml):
        self.renderer.notify_xml_render_end(self, xml)
