from xml.dom.minidom import Element, Text

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
    codehilite_clone = codehilite.cloneNode(True)
    for child_ in html_code.childNodes:
        child = child_.cloneNode(True)
        codehilite.appendChild(child)
    codehilite.removeChild(html_pre)
    return odt_node


def attribute_class(html_node):
    return html_node.getAttribute('class')
