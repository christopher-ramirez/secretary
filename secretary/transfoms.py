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
    elif html_node_class == 'footnotes':
        return transform_footnotes(renderer, xml_object, html_node)
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


def transform_footnotes(render, xml_object, footnote_node):
    # Iterate through Paragraphs in list items to get the
    odt_node = xml_object.createElement('text:p')
    odt_node.setAttribute('text:style-name', 'codehilite')

    for idx, footnote in enumerate(footnote_node.getElementsByTagName('p')):
        text = footnote.childNodes[0].wholeText
        ref = footnote.childNodes[1].getAttribute('href')
        # TODO: check if ref an anchor (#fnref-1)

        note = xml_object.createElement('text:note')
        note.setAttribute('text:id', ref)
        note.setAttribute('text:note-class', 'footnote')

        note_cite = xml_object.createElement('text:note-citation')
        note_cite.appendChild(xml_object.createTextNode(str(idx)))
        note.appendChild(note_cite)

        note_body = xml_object.createElement('text:note-body')
        note_p = xml_object.createElement('text:p')
        note_p.appendChild(xml_object.createTextNode(text))
        note_body.appendChild(note_p)
        note.appendChild(note_body)

        sup_node = None
        for sup in xml_object.getElementsByTagName('sup'):
            if sup.getAttribute('id') == ref[1:]:
                sup_node = sup
                break
        if sup_node:
            sup_node.parentNode.replaceChild(note, sup_node)

    footnote_node.parentNode.removeChild(footnote_node)
    return None


def transform_pre(render, xml_object, pre_node):
    odt_node = xml_object.createElement('text:p')
    odt_node.setAttribute('text:style-name', 'codehilite')

    code_node = pre_node.firstChild
    text_node = code_node.firstChild
    code = text_node.wholeText
    for element in __parse_line(code, xml_object):
        pre_node.appendChild(element)

    pre_node.removeChild(code_node)
    return odt_node


def transform_code(render, xml_object, code_node):
    odt_node = xml_object.createElement('text:p')
    odt_node.setAttribute('text:style-name', 'codehilite')

    text_node = code_node.firstChild
    odt_node.appendChild(text_node)
    return odt_node


def transform_table(render, xml_object, table_node):
    odt_node = xml_object.createElement('table:table')
    odt_node.setAttribute('table:style-name', 'Table')
    odt_column = xml_object.createElement('table:table-column')
    odt_node.appendChild(odt_column)

    for table_row in table_node.getElementsByTagName('tr'):
        table_cells = table_row.getElementsByTagName('td') + table_row.getElementsByTagName('th')
        odt_column.setAttribute('table:number-columns-repeated', str(len(table_cells)))
        odt_row = xml_object.createElement('table:table-row')
        odt_node.appendChild(odt_row)
        for table_cell in table_cells:
            odt_cell = xml_object.createElement('table:table-cell')
            odt_cell.setAttribute('office:value-type', 'string')
            odt_row.appendChild(odt_cell)

            paragraph_node = xml_object.createElement('p')
            for child in table_cell.childNodes:
                if isinstance(child, Element) and child.tagName in ['p', 'pre', 'code', 'div']:
                    odt_cell.appendChild(child.cloneNode(True))
                else:
                    paragraph_node.appendChild(child.cloneNode(True))
            if paragraph_node.hasChildNodes():
                odt_cell.appendChild(paragraph_node)

    table_node.parentNode.replaceChild(odt_node, table_node)
    return None


def attribute_class(html_node):
    return html_node.getAttribute('class')
