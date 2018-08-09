from unittest import TestCase
from xml.dom.minidom import parseString
from jinja2 import Environment
from secretary import Renderer
from secretary.renders.base import RenderJob
from secretary.renders.xmlrender import XMLRender

SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<body xmlns:text="http://localhost/"
        text:text-input="http://localhost/">
    <table>
        <row>
            <text:text-input>{% for name in names %}</text:text-input>
        </row>
        <paragraph>
            <text:text-input>{{ name }}</text:text-input>
        </paragraph>
        <row>
            <text:text-input>{% endfor %}</text:text-input>
        </row>
    </table>
</body>
"""

# Init environment and disable autoescape for testing some parts of the code
env = Environment(extensions=['jinja2.ext.AutoEscapeExtension'])
env.autoescape = False

class XMLRenderTestCase(TestCase):
    def setUp(self):
        self.render = Renderer(env)
        self.job = RenderJob(self.render, None)

    def test_autoescape(self):
        xml_renderer = XMLRender(self.job, SAMPLE_XML)
        expected = ''.join([
            '{% autoescape true %}', SAMPLE_XML, '{% endautoescape %}'])
        self.assertEqual(
            xml_renderer.autoescape_for_xml(SAMPLE_XML), expected)

    def test_prepare_tags(self):
        template = parseString(SAMPLE_XML)
        renderer = XMLRender(self.job, template)
        renderer.prepare_tags()

        out = template.toxml()
        self.assertNotIn('<text:text-input>{% for name in names %}', out)
        self.assertIn('{% for name in names %}\n', out)
        self.assertNotIn('<text:text-input>{{ name }}</text:text-input>', out)
        self.assertIn('{% endfor %}\n', out)
        self.assertIn('<text:span>{{ name }}</text:span>', out)

    def test_render(self):
        xml_renderer = XMLRender(self.job, parseString(SAMPLE_XML))
        results = xml_renderer.render(names=['Chris', 'Michael'])
        self.assertIn('<text:span>Chris</text:span>', results)
        self.assertIn('<text:span>Michael</text:span>', results)

