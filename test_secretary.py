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

    def test__unescape_entities(self):
        test_samples = {
            # test scaping of &gt;
            '{{ "greater_than_1" if 1&gt;0 }}'               : '{{ "greater_than_1" if 1>0 }}',
            '{% a &gt; b %}'                                 : '{% a > b %}',
            '{{ a &gt; b }}'                                 : '{{ a > b }}',
            '{% a|filter &gt; b %}'                          : '{% a|filter > b %}',
            '<node>{% a == b %}</node>{% else if a &gt; b %}': '<node>{% a == b %}</node>{% else if a > b %}',

            # test scaping of &lt; and &quot;
            '{{ &quot;lower_than_1&quot; if 1&lt;0 }}'       : '{{ "lower_than_1" if 1<0 }}',
            '{% a &lt; b %}'                                 : '{% a < b %}',
            '{{ a &lt; b }}'                                 : '{{ a < b }}',
            '{% a|filter &lt; b %}'                          : '{% a|filter < b %}',
            '<node>{% a == b %}</node>{% else if a &lt; b %}': '<node>{% a == b %}</node>{% else if a < b %}',
            
            # test scapig of multiple spaces, even encoded as <text:space> nodes
            '{{ if  <text:s> multiple_spaces }}'                      : '{{ if    multiple_spaces }}',
            '{{ if  </text:s> multiple_spaces }}'                     : '{{ if    multiple_spaces }}',
            '{{ if  <text:s/> multiple_spaces }}'                     : '{{ if    multiple_spaces }}',
            '{{ if <text:span/>[1,2,3]<text:span>&lt;</text:span>2 }}': '{{ if  [1,2,3] < 2 }}',
        }

        for test, expect in test_samples.items():
            assert self.engine._unescape_entities(test) == expect

    def test__encode_escape_chars(self):
        test_samples = {
            '<text:a>\n</text:a>': '<text:a><text:line-break/></text:a>',
            '<text:h>\n</text:h>': '<text:h><text:line-break/></text:h>',
            '<text:p>\n</text:p>': '<text:p><text:line-break/></text:p>',
            '<text:p>Hello\n</text:p>': '<text:p>Hello<text:line-break/></text:p>',
            '<text:p>Hello\nWorld\n!</text:p>': '<text:p>Hello<text:line-break/>World<text:line-break/>!</text:p>',
            '<text:ruby-base>\n</text:ruby-base>': '<text:ruby-base><text:line-break/></text:ruby-base>',
            '<text:meta>\u0009</text:meta>': '<text:meta><text:tab/></text:meta>',
            '<text:meta-field>\n</text:meta-field>': '<text:meta-field><text:line-break/></text:meta-field>',
        }

        for test, expect in test_samples.items():
            assert self.engine._encode_escape_chars(test) == expect

    def test_create_test_node(self):
        assert self.engine.create_text_node(self.document, 'text').toxml() == 'text'

    def test_create_text_span_node(self):
        assert self.engine.create_text_span_node(self.document, 'text').toxml() == '<text:span>text</text:span>'

