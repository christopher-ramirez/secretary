import re
import logging
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError, ErrorString


class JinjaSafeTags(object):
    """A class used as an interface for working with jinja tags delimeters."""
    def __init__(self, environment):
        self.environment = environment
        self._compile_tags()
        self._compile_escape_expressions()

    def _compile_tags(self):
        self.tag_pattern = re.compile(r'(?is)^({0}|{1}).*({2}|{3})$'.format(
            self.environment.variable_start_string,
            self.environment.block_start_string,
            self.environment.variable_end_string,
            self.environment.block_end_string
        ))

        self.block_pattern = re.compile(r'(?is)^{0}.*{1}$'.format(
            self.environment.block_start_string,
            self.environment.block_end_string
        ))

    def _compile_escape_expressions(self):
        self.escape_map = dict()
        unescape_rules = {
            r'&gt;': r'>',
            r'&lt;': r'<',
            r'&amp;': r'&',
            r'&quot;': r'"',
            r'&apos;': r'\'',
        }

        for key, value in unescape_rules.items():
            exp = r'(?is)(({0}|{1})[^{3}{4}]*?)({2})([^{0}{1}]*?({3}|{4}))'
            key = re.compile(exp.format(
                self.environment.variable_start_string,
                self.environment.block_start_string,
                key,
                self.environment.variable_end_string,
                self.environment.block_end_string
            ))

            self.escape_map[key] = r'\1{0}\4'.format(value)

    def is_tag(self, tag):
        """Returns True if tag is a valid jinja instruction tag."""
        return len(self.tag_pattern.findall(tag)) > 0

    def is_block_tag(self, tag):
        """Returns True is tag is a jinja flow control tag."""
        return len(self.block_pattern.findall(tag)) > 0

    def unescape_entities(self, xml_text):
        """
        Unescape links and '&amp;', '&lt;', '&quot;' and '&gt;' within jinja
        instructions. The regexs rules used here are compiled in
        _compile_escape_expressions.
        """
        for regexp, replacement in self.escape_map.items():
            while True:
                xml_text, substitutions = regexp.subn(replacement, xml_text)
                if not substitutions:
                    break

        return self._unescape_links(xml_text)

    def _unescape_links(self, xml_text):
        """Fix Libreoffice auto escaping of xlink:href attribute values.
        This unescaping is only done on 'secretary' scheme URLs."""
        import urllib
        robj = re.compile(r'(?is)(xlink:href=\")secretary:(.*?)(\")')

        def replacement(match):
            return ''.join([match.group(1), urllib.unquote(match.group(2)),
                            match.group(3)])

        while True:
            xml_text, rep = robj.subn(replacement, xml_text)
            if not rep:
                break

        return xml_text

class XMLRender(object):
    def __init__(self, job, XMLDocument):
        self.job = job
        self.jt = JinjaSafeTags(job.renderer.environment)
        self.document = XMLDocument

    def render(self, **kwargs):
        """Returns a rendered XML string. Data is passed to this function as kwargs."""
        self.prepare_tags()
        template_source = self.jt.unescape_entities(self.document.toxml())
        template_object = self.job.renderer.environment.from_string(template_source)
        result = self.encode_feed_chars(template_object.render(**kwargs))

        return result

    def prepare_tags(self):
        """ Here we search for every field node present in xml_document.
        For each field we found we do:
        * if field is a print field ({{ field }}), we replace it with a
          <text:span> node.

        * if field is a control flow ({% %}), then we find immediate node of
          type indicated in field's `text:description` attribute and replace
          the whole node and its childrens with field's content.

          If `text:description` attribute starts with `before::` or `after::`,
          then we move field content before or after the node in description.

          If no `text:description` is available, find the immediate common
          parent of this and any other field and replace its child and
          original parent of field with the field content.

          e.g.: original
          <table>
              <table:row>
                  <field>{% for bar in bars %}</field>
              </table:row>
              <paragraph>
                  <field>{{ bar }}</field>
              </paragraph>
              <table:row>
                  <field>{% endfor %}</field>
              </table:row>
          </table>

          After processing:
          <table>
              {% for bar in bars %}
              <paragraph>
                  <text:span>{{ bar }}</text:span>
              </paragraph>
              {% endfor %}
          </table>
        """

        self._census_tags()
        map(self._prepare_tag, self.tags_in_document())

    def _census_tags(self):
        for tag in self.tags_in_document():
            content = tag.childNodes[0].data.strip()
            is_block_tag = self.jt.is_block_tag(content)
            self.count_node_decendant_tags(tag.parentNode, is_block_tag)

    def tags_in_document(self):
        """Yields a list if template tags in current document."""
        for tag in self.document.getElementsByTagName('text:text-input'):
            if not tag.hasChildNodes():
                continue

            content = tag.childNodes[0].data.strip()
            if not self.jt.is_tag(content):
                continue

            yield tag

    @staticmethod
    def count_node_decendant_tags(node, is_block_tag):
        """Increate *node* tags_count property and block_count property
        if *is_block_tag* is True. Otherwise increase *var_count* property.
        This is also done recursevely for this node parents."""
        if not node:
            return

        # start counter
        for attr in ['tags_count', 'block_count', 'var_count']:
            if not hasattr(node, attr):
                setattr(node, attr, 0)

        node.tags_count += 1
        setattr(node, 'block_count' if is_block_tag else 'var_count',
                getattr(node, 'block_count' if is_block_tag else 'var_count') + 1)
        XMLRender.count_node_decendant_tags(node.parentNode, is_block_tag)

    def _prepare_tag(self, tag):
        from constants import FLOW_REFERENCES
        # We have to replace a node, let's call it "placeholder", with the
        # content of our jinja tag. The placeholder can be a node with all its
        # children. Node's "text:description" attribute indicates how far we
        # can scale up in the tree hierarchy to get our placeholder node. When
        # said attribute is not present, then we scale up until we find a
        # common parent for this tag and any other tag.
        input_node = tag
        content = tag.childNodes[0].data.strip()
        is_block = self.jt.is_block_tag(content)
        take_upto = tag.getAttribute('text:description').strip().lower()

        # TODO: Lets filters override "take_upto" value

        if take_upto:
            __ = FLOW_REFERENCES.get(take_upto, FLOW_REFERENCES)
            input_node = self.node_parent_of_name(tag, __) or input_node
            final_node = self.create_text_node(content)
        elif is_block:
            # Expand field node until a shared parent if found
            while not input_node.parentNode.tags_count > 1:
                input_node = input_node.parentNode
            if input_node:
                final_node = self.create_text_node(content)
        else:
            # Default handling for vars tags or misconfigured block tags
            final_node = self.create_span_node(content)

        input_parent = input_node.parentNode
        if not take_upto.startswith('after::'):
            input_parent.insertBefore(final_node, input_node)
        else:
            if input_node.isSameNode(input_parent.lastChild):
                input_parent.appendChild(final_node)
            else:
                input_parent.insertBefore(final_node, input_node.nextSibling)

        if take_upto.startswith(('after::', 'before::')):
            # Don't remove whole field tag, only "text:text-input" container
            input_node = self.node_parent_of_name(tag, 'text:p')
            input_parent = input_node.parentNode

        # Finally remove the original input field node
        input_parent.removeChild(input_node)

    @staticmethod
    def node_parent_of_name(node, name):
        """Returns the node's parent with name equal to *name*.
        Returns None if a parent with that name is not found."""
        if not hasattr(node, 'parentNode'):
            return None

        if node.parentNode.nodeName.lower() == name.lower():
            return node.parentNode

        # Look into node's grandparent
        return XMLRender.node_parent_of_name(node.parentNode, name)

    def create_text_node(self, text):
        return self.document.createTextNode(text)

    def create_span_node(self, content):
        span_elem = self.document.createElement('text:span')
        span_content = self.create_text_node(content)
        span_elem.appendChild(span_content)
        return span_elem

    @staticmethod
    def encode_feed_chars(xml_text):
        """Replace line feed and/or tabs within text:span entities."""
        find_pattern = r'(?is)<text:([\S]+?).*?>([^>]*?([\n\t])[^<]*?)</text:\1>'
        for m in re.finditer(find_pattern, xml_text):
            content = m.group(0)
            replacement = content.replace('\n', '<text:line-break/>')
            replacement = replacement.replace('\t', '<text:tab/>')
            xml_text = xml_text.replace(content, replacement)

        return xml_text
