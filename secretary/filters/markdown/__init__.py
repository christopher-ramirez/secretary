'''
    Implements Secretary's "markdown" filter.
'''

import re
from xml.dom import Node
from xml.dom.minidom import parseString
from markdown2 import markdown
from jinja2 import Markup
from .markdown_map import transform_map

from ..base import SecretaryFilterInterface

class MarkdownFilter(SecretaryFilterInterface):
    '''markdown filter implemetation.'''

    def render(self, value, *args, **kwargs):
        '''
        Converts markdown value into an ODT formmated text.
        '''
        html_object = self.markdown_to_html(value)

        # Transform every known HTML tags to odt
        map(lambda k, v: self.transform_html_tags_to_odt(html_object, k, v),
            transform_map.items())

        def _node_to_str(node):
            result = node.toxml()

            # Convert single linebreaks in preformatted nodes to text:line-break
            if node.__class__.__name__ != 'Text' and \
                    node.getAttribute('text:style-name') == 'Preformatted_20_Text':
                result = result.replace('\n', '<text:line-break/>')

            # All double linebreaks should be converted to an empty paragraph
            return result.replace('\n\n', '<text:p text:style-name="Standard"/>')

        str_nodes = map(_node_to_str,
                        html_object.getElementsByTagName('html')[0].childNodes)
        return Markup(''.join([node for node in str_nodes]))

    @staticmethod
    def markdown_to_html(value):
        '''
        Converts markdown value to HTML, returning a parsed XML object.
        '''
        html = markdown(value)
        return parseString(
            '<html>{}</html>'.format(html.encode('ascii', 'xmlcharrefreplace'))
        )

    def transform_html_tags_to_odt(self, html, tag_name, transform_props):
        '''Transform all tags of a kind in html into the corresponging ODT tag.
        How the tags are tranformed is defined in transform_prop param.'''
        html_tags = html.getElementsByTagName(tag_name)
        map(lambda t: self.html_tag_to_odt(html, t, transform_props), html_tags)

    def html_tag_to_odt(self, html, tag, transform):
        '''
        Replace tag in html with a new odt tag created from the instructions
        in tranform dictionary.
        '''
        odt_tag = html.createElement(transform['replace_with'])

        # First lets work with the content
        if tag.hasChildNodes():
            # Only when there's a double linebreak separating list elements,
            # markdown2 wraps the content of the element inside a <p> element.
            # In ODT we should always encapsulate list content in a single paragraph.
            # Here we create the container paragraph in case markdown didn't.
            if tag.localName == 'li' and tag.childNodes[0].localName != 'p':
                container = html.createElement('text:p')
                odt_tag.appendChild(container)
            elif tag.localName == 'code':
                def traverse_preformated(node):
                    if node.hasChildNodes():
                        for n in node.childNodes:
                            traverse_preformated(n)
                    else:
                        container = html.createElement('text:span')
                        for text in re.split('(\n)', node.nodeValue.lstrip('\n')):
                            if text == '\n':
                                container.appendChild(html.createElement('text:line-break'))
                            else:
                                container.appendChild(html.createTextNode(text))

                        node.parentNode.replaceChild(container, node)
                traverse_preformated(tag)
                container = odt_tag
            else:
                container = odt_tag

            # Insert html tag content (actually a group of child nodes)
            map(lambda child: container.appendChild(child.cloneNode(True)),
                tag.childNodes)

        # Now tranform tag attributes
        if 'style_attributes' in transform:
            map(lambda attr, value: odt_tag.setAttribute('text:{}'.format(attr), value),
                transform['style_attributes'].items())

        if 'attributes' in transform:
            map(lambda attr, value: odt_tag.setAttribute(attr, value),
                transform['attributes'].items())

            # Special handling of <a> tags and their href attribute
            if tag.localName == 'a' and tag.hasAttribute('href'):
                odt_tag.setAttribute('xlink:href', tag.getAttribute('href'))

        # Does we need to create a style for displaying this tag?
        if 'style' in transform and \
                (not transform['style']['name'] in self.styles_cache):
            style_name = transform['style']['name']
            style = self.get_style_node(style_name)
            if not style:
                style = self.insert_style_in_automatic_styles(
                    style_name, transform['style'].get('attributes', dict()),
                    **transform['style']['properties']
                )
                self.styles_cache[style_name] = style

        tag.parentNode.replaceChild(odt_tag, tag)

    def get_style_node(self, style_name, styles=None):
        '''
        Returns the style node with name equal to style_name found as child of
        <office:automatic-styles> current xml tag. Returns None if not found.
        '''
        styles = styles or self._get_automatic_styles()
        if not styles:
            return None

        for style in styles.childNodes:
            if hasattr(style, 'getAttribute'):
                if style.getAttribute('style:name') == style_name:
                    return style

    def insert_style_in_automatic_styles(self, name, attrs={}, **props):
        '''
        Inserts a style into automatic styles and returns the node created.
        '''
        auto_styles = self._get_automatic_styles()
        if not auto_styles:
            return

        style = self.xml.createElement('style:style')
        style.setAttribute('style:name', name)
        style.setAttribute('style:family', 'text')
        style.setAttribute('style:parent-style-name', 'Standard')

        map(lambda attr, val: style.setAttribute('style:{}'.format(attr), val),
            attrs.items())

        if props:
            style_props = self.xml.createElement('style:text-properties')
            map(lambda attr, val: style_props.setAttribute(attr, val), props.items())
            style.appendChild(style_props)

        return auto_styles.appendChild(style)

    def _get_office_styles(self):
        office_styles = self.xml.getElementsByTagName('office:styles')
        if not office_styles:
            return None

        return office_styles[0]

    def _get_automatic_styles(self):
        automatic_styles = self.xml.getElementsByTagName('office:automatic-styles')
        if not automatic_styles:
            return None

        return automatic_styles[0]

    def before_render_xml(self, renderer, job, xml):
        self.xml = xml
        self.styles_cache = dict()
        self._create_markdown_code_style()

    def after_render_xml(self, renderer, job, xml):
        self.xml = None

    def _create_markdown_code_style(self):
        # Creates a monospace style to use for <code> tags. This new styles
        # inherits from 'Preformatted_20_Text'.
        preformatted = self.get_style_node('Preformatted_20_Text',
                                           self._get_office_styles())
        if not preformatted:
            return

        text_props = preformatted.getElementsByTagName('style:text-properties')[0]
        style_props = {
            'style:font-name': '',
            'fo:font-family': '',
            'style:font-family-generic': '',
            'style:font-pitch': ''
        }

        map(lambda k: style_props.update(**{k: text_props.getAttribute(k)}),
            style_props.keys())

        self.insert_style_in_automatic_styles('markdown_code', {}, **style_props)
        self.styles_cache['markdown_code'] = True
