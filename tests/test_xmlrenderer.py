from unittest import TestCase
from xml.dom.minidom import parseString
from jinja2 import Environment
from secretary import Renderer
from secretary.renders.base import RenderJob
from secretary.renders.xmlrender import XMLRender

SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<note>
  {% for name in names %}
  <to>{{ name }}</to>
  {% endfor %}
</note>
"""

# Init environment and disable autoescape for testing some parts of the code
env = Environment()
env.autoescape = False

class XMLRenderTestCase(TestCase):
    def setUp(self):
        self.render = Renderer(env)
        self.job = RenderJob(self.render, SAMPLE_XML)
        self.xmlrenderer = XMLRender(self.job, SAMPLE_XML)

    def test_autoescape(self):
        final = ''.join([
            '{% autoescape true %}', SAMPLE_XML, '{% endautoescape %}'])
        self.assertEqual(self.xmlrenderer.autoescape_for_xml(SAMPLE_XML), final)

    def test_prepare_tags(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <body xmlns:text="http://localhost/"
              text:text-input="http://localhost/">
            <table>
              <row>
                  <text:text-input>{% for bar in bars %}</text:text-input>
              </row>
              <paragraph>
                  <text:text-input>{{ bar }}</text:text-input>
              </paragraph>
              <row>
                  <text:text-input>{% endfor %}</text:text-input>
              </row>
            </table>
        </body>
        """
        template = parseString(xml)
        render = XMLRender(self.job, template)
        render.prepare_tags()

        fixedXml = template.toxml()
        self.assertNotIn('<text:text-input>{% for bar in bars %}', fixedXml)
        self.assertIn('{% for bar in bars %}\n', fixedXml)
        self.assertNotIn('<text:text-input>{% endfor %}', fixedXml)
        self.assertIn('{% endfor %}\n', fixedXml)
        self.assertIn('<text:span>{{ bar }}</text:span>', fixedXml)

    def test_render(self):
        template = parseString(SAMPLE_XML)
        job = XMLRender(self.job, template)
        results = job.render(names=['Chris', 'Michael'])
        self.assertIn('<to>Chris</to>', results)
        self.assertIn('<to>Michael</to>', results)

