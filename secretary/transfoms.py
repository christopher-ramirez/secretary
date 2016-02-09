import re
from xml.dom.minidom import Element, Text


def __parse_line(line, xml_object):
    # Find tabs spaces
    nodes = []
    index = 0
    for matched in re.finditer('(\\\\n|\\n|    |\t| )', line):
        start, end = matched.span()
        if start > index:
            chunk = line[index:start]
            obj = xml_object.createTextNode(chunk)
            nodes.append(obj)
        text = matched.group()
        if text in ["\\n", "\\\\n"]:
            obj = xml_object.createElement('text:line-break')
            nodes.append(obj)
        elif text in ['    ', '\t']:
            obj = xml_object.createElement('text:tab')
            nodes.append(obj)
        elif text in [' ']:
            obj = xml_object.createTextNode(' ')
            nodes.append(obj)
        index = end
    if not matched:
        obj = xml_object.createTextNode(line)
        nodes.append(obj)
    return nodes


def transform_div(renderer, xml_object, html_node):
    """Removes HTML sup tags with `footnote-ref` class name. it's part of creating footnote process.
    """
    html_node_class = html_node.getAttribute('class')
    if html_node_class == 'codehilite':
        return transform_codelilite(renderer, xml_object, html_node)
    return xml_object.createElement('text:p')


def transform_codelilite(renderer, xml_object, codehilite):
    odt_node = xml_object.createElement('text:p')
    odt_node.setAttribute('text:style-name', 'codehilite')
    # get pre and code tags
    html_pre = codehilite.firstChild
    html_code = html_pre.firstChild

    # move tags in code tag to codehilite tag
    for child_ in html_code.childNodes:
        if isinstance(child_, Text):
            code = child_.wholeText
            for element in __parse_line(code, xml_object):
                codehilite.appendChild(element)
        else:
            child = child_.cloneNode(True)
            codehilite.appendChild(child)
    codehilite.removeChild(html_pre)
    return odt_node


def transform_code(render, xml_object, pre_node):
    odt_node = xml_object.createElement('text:p')
    odt_node.setAttribute('text:style-name', 'codehilite')

    code_node = pre_node.firstChild
    text_node = code_node.firstChild
    code = text_node.wholeText
    for element in __parse_line(code, xml_object):
        pre_node.appendChild(element)

    pre_node.removeChild(code_node)
    return odt_node

def attribute_class(html_node):
    return html_node.getAttribute('class')
