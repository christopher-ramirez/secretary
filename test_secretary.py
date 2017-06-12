# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from xml.dom.minidom import getDOMImplementation
from unittest import TestCase
from secretary import UndefinedSilently, Renderer

def test_undefined_silently():
    undefined = UndefinedSilently()

    assert isinstance(undefined(), UndefinedSilently)
    assert isinstance(undefined.attribute, UndefinedSilently)
    assert str(undefined) == ''

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

class EncodeLFAndFWithinTextNamespace(TestCase):
    """Test encoding of line feed and tab chars within text: namespace"""
    def test_encode_linefeed_char(self):
        xml = '<text:span>This\nLF</text:span>'
        espected = '<text:span>This<text:line-break/>LF</text:span>'
        assert (Renderer._encode_escape_chars(xml) == espected)

    def test_encode_tab_char(self):
        xml = '<text:span>This\tTab</text:span>'
        espected = '<text:span>This<text:tab/>Tab</text:span>'
        assert (Renderer._encode_escape_chars(xml) == espected)

    def test_escape_elem_with_attributes(self):
        """A bug in _encode_escape_chars was preventing it from escaping
        LF and tabs inside text elements with tag attributes. See:
        https://github.com/christopher-ramirez/secretary/issues/39"""
        xml = '<text:span attr="value">This\nLF</text:span>'
        espected = '<text:span attr="value">This<text:line-break/>LF</text:span>'
        assert (Renderer._encode_escape_chars(xml) == espected)
