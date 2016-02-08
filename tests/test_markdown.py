# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import os
from unittest import TestCase, main, skip
from secretary import Renderer
from secretary.utils import UndefinedSilently, pad_string


def test_undefined_silently():
    undefined = UndefinedSilently()

    assert isinstance(undefined(), UndefinedSilently)
    assert isinstance(undefined.attribute, UndefinedSilently)
    assert str(undefined) == ''


def test_pad_string():
    assert pad_string('TEST') == '0TEST'
    assert pad_string('TEST', 4) == 'TEST'
    assert pad_string(1) == '00001'


class MarkdownFilterTestCase(TestCase):
    def setUp(self):
        self.engine = Renderer(markdown_extras=['fenced-code-blocks'])
        self.engine.template_images = {}

    def test_paragraphs(self):
        test_samples = {
            'hello\n\n\nworld\n': 2,
            'hello world': 1,
        }
        pattern = r'<text:p text:style-name="Standard">[a-z ]+</text:p>'
        for test, occurances in test_samples.items():
            result = self.engine.markdown_filter(test)
            found = re.findall(pattern , result)
            assert len(found) == occurances

    def test_fenced_code_blocks(self):
        test_samples = {
            "```python\ndef test():\n    pass\n```": ''
        }
        for test, expected in test_samples.items():
            result = self.engine.markdown_filter(test)
            assert not 'python' in result

    @skip
    def test_images(self):
        test_samples = {
            'Hello world ![sample](samples/images/writer.png)\n': 1,
            '![sample](samples/images/writer.png)\n': 1,
            '![sample](samples/images/writer.png)\n![sample](samples/images/writer.png)\n': 2,
        }
        pattern = '<draw:frame draw:name="[0-9a-z]+"><draw:image/></draw:frame>'
        for test, occurances in test_samples.items():
            result = self.engine.markdown_filter(test)
            found = re.findall(pattern , result)
            assert len(found) == occurances

    @skip
    def test_footnotes(self):
        test_samples = {
            'hello world. [^1]\n\n[^1]: referenced.\n\n': '<text:p text:style-name="Standard">hello world. <text:note text:id="fn-1" text:note-class="footnote"><text:note-citation>1</text:note-citation><text:note-body><text:p>referenced. </text:p></text:note-body></text:note></text:p>',
            'foo. [^1]\n bar. [^2] \n\n[^1]: referenced by foo.\n[^2]: referenced by bar\n': '<text:p text:style-name="Standard">foo. <text:note text:id="fn-1" text:note-class="footnote"><text:note-citation>1</text:note-citation><text:note-body><text:p>referenced by foo. </text:p></text:note-body></text:note> bar. <text:note text:id="fn-2" text:note-class="footnote"><text:note-citation>2</text:note-citation><text:note-body><text:p>referenced by bar </text:p></text:note-body></text:note> </text:p>',
            }
        for test, expected in test_samples.items():
            result = self.engine.markdown_filter(test)
            assert expected in result
