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
        }

        for test, expect in test_samples.items():
            assert self.engine._unescape_entities(test) == expect

    def _test_is_jinja_tag(self):
        assert self._is_jinja_tag('{{ foo }}')==True
        assert self._is_jinja_tag('{ foo }')==False

    def _test_is_block_tag(self):
        assert self._is_block_tag('{% if True %}')==True
        assert self._is_block_tag('{{ foo }}')==False
        assert self._is_block_tag('{ foo }')==False

    def test_create_test_node(self):
        assert self.engine.create_text_node(self.document, 'text').toxml() == 'text'

    def test_create_text_span_node(self):
        assert self.engine.create_text_span_node(self.document, 'text').toxml() == '<text:span>text</text:span>'


class EscapingVariablesValues(TestCase):
    """
        Test encoding of line feed and tab variables valuess
    """
    def test_encode_linefeed_char(self):
        xml = 'This\nLF'
        expected = 'This<text:line-break/>LF'
        assert (Renderer.get_escaped_var_value(xml) == expected)

    def test_encode_linefeed_char(self):
        xml = 'This\tTab char'
        expected = 'This<text:tab/>Tab char'
        assert (Renderer.get_escaped_var_value(xml) == expected)

    def test_escape_xml_reserved_chars(self):
        ''' Should also escape minor and mayor signs '''
        xml = '1 is > than 0 & -1 is <'
        expected = '1 is &gt; than 0 &amp; -1 is &lt;'
        assert (Renderer.get_escaped_var_value(xml) == expected)
