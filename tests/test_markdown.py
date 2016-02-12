# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import os
from unittest import TestCase, main
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
        self.engine = Renderer(markdown_extras=['fenced-code-blocks', 'footnotes'])
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
        test = "```python\ndef test():\n    pass\n```"
        result = self.engine.markdown_filter(test)
        assert not 'python' in result

    def test_code_blocks(self):
        test = "```\ndef test():\n    pass\n```"
        result = self.engine.markdown_filter(test)
        assert 'codehilite' in result

    def test_code(self):
        test = "`test code`"
        result = self.engine.markdown_filter(test)
        assert 'codehilite' in result

    def test_code_blocks_indents(self):
        test_samples = {
            "```python\ndef test():\n    if True:\n        pass\n```": 3,
            "```\ndef test():\n    pass\n```": 1,
        }
        for test, occurances in test_samples.items():
            result = self.engine.markdown_filter(test)
            assert result.count('<text:tab/>') == occurances

    def test_new_line(self):
        test = "```python\ndef test():\n    pass\n```"
        result = self.engine.markdown_filter(test)
        assert not '\n' in result

    def test_footnotes(self):
        tests = (("foo. [^1]\n bar. [^2] \n\n[^1]: referenced by foo.\n[^2]: referenced by bar\n",
                  '<text:p text:style-name="Standard">foo. <text:note text:id="#fnref-1" text:note-class="footnote"><text:note-citation>0</text:note-citation><text:note-body><text:p>referenced by foo.\xa0</text:p></text:note-body></text:note><text:line-break/> bar. <text:note text:id="#fnref-2" text:note-class="footnote"><text:note-citation>1</text:note-citation><text:note-body><text:p>referenced by bar\xa0</text:p></text:note-body></text:note> </text:p>'),
                 ("""# TEST

foo. [^1]\n bar. [^2] \n\n[^1]: referenced by foo.\n[^2]: referenced by bar\n

asdasdasd asd asd
""", '<text:p text:style-name="Heading_20_1">TEST</text:p><text:line-break/><text:line-break/><text:p text:style-name="Standard">foo. <text:note text:id="#fnref-1" text:note-class="footnote"><text:note-citation>0</text:note-citation><text:note-body><text:p>referenced by foo.\xa0</text:p></text:note-body></text:note><text:line-break/> bar. <text:note text:id="#fnref-2" text:note-class="footnote"><text:note-citation>1</text:note-citation><text:note-body><text:p>referenced by bar\xa0</text:p></text:note-body></text:note> </text:p><text:line-break/><text:line-break/><text:p text:style-name="Standard">asdasdasd asd asd</text:p><text:line-break/><text:line-break/><text:line-break/>'),
                )
        for text, expected in iter(tests):
            result = self.engine.markdown_filter(text)
            assert expected in result

    def test_tables(self):
        text = "<table><tr><td>1</td><td>2</td></tr><tr><td>3</td><td>4</td></tr></table>"
        expected = ('<table:table table:style-name="Table">'
                    '<table:table-column table:number-columns-repeated="2"/>'
                    '<table:table-row>'
                    '<table:table-cell office:value-type="string">'
                    '<text:p text:style-name="Standard">1</text:p>'
                    '</table:table-cell>'
                    '<table:table-cell office:value-type="string">'
                    '<text:p text:style-name="Standard">2</text:p>'
                    '</table:table-cell>'
                    '</table:table-row>'
                    '<table:table-row>'
                    '<table:table-cell office:value-type="string">'
                    '<text:p text:style-name="Standard">3</text:p>'
                    '</table:table-cell>'
                    '<table:table-cell office:value-type="string">'
                    '<text:p text:style-name="Standard">4</text:p>'
                    '</table:table-cell>'
                    '</table:table-row>'
                    '</table:table>')
        result = self.engine.markdown_filter(text)
        assert expected in result
