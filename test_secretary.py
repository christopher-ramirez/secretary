# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from xml.dom.minidom import getDOMImplementation
from unittest import TestCase
from secretary import UndefinedSilently, pad_string, Renderer

def test_undefined_silently():
    undefined = UndefinedSilently()

    assert isinstance(undefined(), UndefinedSilently)
    assert isinstance(undefined.attribute, UndefinedSilently)
    assert str(undefined) == ''

def test_pad_string():
    assert pad_string('TEST') == '0TEST'
    assert pad_string('TEST', 4) == 'TEST'
    assert pad_string(1) == '00001'

class RenderTestCase(TestCase):
    def setUp(self):
        root = os.path.dirname(__file__)
        impl = getDOMImplementation()
        template = os.path.join(root, 'simple_template.odt')

        self.document = impl.createDocument(None, "some_tag", None)
        self.engine = Renderer()
        self.engine.render(template)

    def test_create_test_node(self):
        assert self.engine.create_text_node(self.document, 'text').toxml() == 'text'

    def test_create_text_span_node(self):
        assert self.engine.create_text_span_node(self.document, 'text').toxml() == '<text:span>text</text:span>'

