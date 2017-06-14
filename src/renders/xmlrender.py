'''
    Implements XMLRender class.

    XMLRender is responsible for adapting an ODT XML document so it can
    be transformed rendered using Jinja2.

    The two key functions XMLRender performs are:
    1.  Transform "text:text-input" tags to text:span when these are variables
        of Text node elements when these are flow control tags.
    2.  Adapt and move flow control tags so they perform the desired functionallity.
'''

import re
from base import JinjaTagsUtils

class XMLRender(object):
    '''
    Renders a XML document of OpenDocument format.
    '''
    def __init__(self, job, XMLDocument):
        self.job = job
        self.tags = JinjaTagsUtils(job.renderer.environment)
        self.document = XMLDocument

    def render(self, **kwargs):
        '''
        Returns a rendered XML string. Template data is passed as kwargs.
        '''
        self.prepare_tags()
        template_source = self.tags.unescape_entities(self.document.toxml())
        template_object = self.job.renderer.environment.from_string(template_source)
        result = self.encode_feed_chars(template_object.render(**kwargs))

        return result

    def prepare_tags(self):
        '''
        Here we search for every field node present in xml_document.
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
        '''

        self._census_tags()
        map(self._prepare_tag, self.tags_in_document())

    def _census_tags(self):
        for tag in self.tags_in_document():
            content = tag.childNodes[0].data.strip()
            is_block_tag = self.tags.is_block_tag(content)
            self.count_node_decendant_tags(tag.parentNode, is_block_tag)

    def tags_in_document(self):
        '''
        Yields a list if template tags in current document.
        '''
        for tag in self.document.getElementsByTagName('text:text-input'):
            if not tag.hasChildNodes():
                continue

            content = tag.childNodes[0].data.strip()
            if not self.tags.is_tag(content):
                continue

            yield tag

    @staticmethod
    def count_node_decendant_tags(node, is_block_tag):
        '''
        Increate *node* tags_count property and block_count property
        if *is_block_tag* is True. Otherwise increase *var_count* property.
        This is also done recursevely for this node parents.
        '''
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
        is_block = self.tags.is_block_tag(content)
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
        '''
        Returns the node's parent with name equal to *name*.
        Returns None if a parent with that name is not found.
        '''
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
        '''
        Replace line feed and/or tabs within text:span entities.
        '''
        find_pattern = r'(?is)<text:([\S]+?).*?>([^>]*?([\n\t])[^<]*?)</text:\1>'
        for m in re.finditer(find_pattern, xml_text):
            content = m.group(0)
            replacement = content.replace('\n', '<text:line-break/>')
            replacement = replacement.replace('\t', '<text:tab/>')
            xml_text = xml_text.replace(content, replacement)

        return xml_text
