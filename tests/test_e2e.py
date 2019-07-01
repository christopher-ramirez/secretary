from unittest import TestCase
from xml.dom.minidom import parseString
from secretary import Renderer

sample_data = {
    'loop': [
        1, True, 0, False, 'A string', u'Unicode V\xe1l\xfc\u1ebds', None,
        'True && True'
    ],
    'site': 'www.github.com'
}

class E2ETest(TestCase):
    def test_render(self):
        engine = Renderer()
        template = open('./tests/e2e.fodt', 'rb')
        output = engine.render(template, **sample_data)

        self.assertIn('Unicode V\xc3\xa1l\xc3\xbc\xe1\xba\xbds', output)
        self.assertIn('True &amp;&amp; True', output)
        self.assertIn('www.github.com', output)
        self.assertIn('True output', output)
        self.assertNotIn('False output', output)

        # Should not raises when parsing final xml
        parseString(output)
