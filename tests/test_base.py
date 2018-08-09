from unittest import TestCase
from jinja2 import Environment
from secretary.renders.base import JinjaTagsUtils


class JinjaTagsUtilsTestCase(TestCase):
    def setUp(self):
        self.environment = Environment()
        self.tu = JinjaTagsUtils(self.environment)

    def test_tag_is_tag(self):
        assert self.tu.is_tag('{{ var }}'), '{{ var }} is a print tag'
        assert not self.tu.is_tag('{ var }'), '{ var } should no be a tag'

    def test_tag_is_block(self):
        assert self.tu.is_block_tag('{% set %}'), '{% set %} is block tag'
        assert not self.tu.is_block_tag('{{ block }}'), \
            '{{ block }} is not a block tag'

    def test_unescape_entities(self):
        tests = {
            u'{{a &amp;&amp; b}}': u'{{a && b}}',
            u'{{a &lt; b}}': u'{{a < b}}',
            u'{{b &gt; a}}': u'{{b > a}}',
            u'{{&quot; Hello &quot;}}': u'{{" Hello "}}',
            u'{{&apos; Hello &apos;}}': u"{{' Hello '}}"
        }

        for t, r in tests.items():
            self.assertEqual(self.tu.unescape_entities(t), r)

    def test_escape_links(self):
        test = '<a xlink:href="secretary:http://example.com/{{a%20b}}"></a>'
        expected = '<a xlink:href="http://example.com/{{ SafeValue(a b) }}"></a>'
        self.assertEqual(self.tu._unescape_links(test), expected)


class RenderJobTestCase(TestCase):
    pass
