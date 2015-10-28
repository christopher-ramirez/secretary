#!/usr/bin/python

from random import randint
try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict
# Transform map used by the markdown filter. transform_map have
# instructions of how to transform a HTML style tag into a ODT document
# styled tag. Some ODT tags may need extra attributes; these are defined
# as a dict in the 'style_attributes' key. Also, some tags may need to create
# new styles in the document.

common_styles = {
	'italic': {
        'replace_with': 'text:span',
        'style_attributes': {
            'style-name': 'markdown_italic'
        },

        'style': {
            'name': 'markdown_italic',
            'properties': {
                'fo:font-style': 'italic',
                'style:font-style-asian': 'italic',
                'style:font-style-complex': 'italic'
            }
        }
    },

    'strong': {
        'replace_with': 'text:span',
        'style_attributes': {
            'style-name': 'markdown_bold'
        },

        'style': {
            'name': 'markdown_bold',
            'properties': {
                'fo:font-weight': 'bold',
                'style:font-weight-asian': 'bold',
                'style:font-weight-complex': 'bold'
            }
        }
    },

    'p': {
        'replace_with': 'text:p',
        'style_attributes': {
            'style-name': 'Standard'
        }
    }
}

def transform_img(renderer, xml_object, html_node):
    """Transforms img tag to ODF draw:frame xml object.
    """
    # register image to be Transfered later using propper media loader.
    image_src = html_node.getAttribute('src')
    image_key = renderer.image_filter(image_src)
    
    frame_node = xml_object.createElement('draw:frame')
    frame_node.setAttribute('draw:name', image_key)
    
    # draw:frame needs a child `draw:image` node
    frame_child = xml_object.createElement('draw:image')
    frame_node.appendChild(frame_child)
    return frame_node

def transform_ol(renderer, xml_object, html_node):
    """Transforms ol tag with class `footnotes` and all the links with
    href value like #fn-* to ODF footnotes xml object.
    """
    if html_node.getAttribute('class') == 'footnotes':
        for child in html_node.getElementsByTagName('ol')[0].childNodes:
            child_id = child.getAttribute('id')
            child_numeric = child_id[3:]
            child_text = child.firstChild.firstChild.nodeValue
            
            footnote_node = xml_object.createElement('text:note')
            footnote_node.setAttribute('text:note-class', 'footnote')
            footnote_node.setAttribute('text:id', child_id)
            
            footnote_citaction = xml_object.createElement('text:note-citation')
            footnote_citaction.appendChild(xml_object.createTextNode(child_numeric))
            footnote_node.appendChild(footnote_citaction)
            
            footnote_body = xml_object.createElement('text:note-body')
            footnote_p = xml_object.createElement('text:p')
            footnote_p.appendChild(xml_object.createTextNode(child_text))
            footnote_body.appendChild(footnote_p)
            
            footnote_node.appendChild(footnote_body)
            element = xml_object.getElementsByTagName('a')
            for element in xml_object.getElementsByTagName('a'):
                if element.getAttribute('href') == '#%s' % child_id:
                    el_parent = element.parentNode
                    element.parentNode.insertBefore(footnote_node, element)
                    element.parentNode.removeChild(element)
            
        html_node.parentNode.removeChild(html_node)

def transform_sup(renderer, xml_object, html_node):
    """Removes HTML sup tags with `footnote-ref` class name. it's part of creating footnote process.
    """
    if html_node.getAttribute('class') == 'footnote-ref':
        node_child = html_node.firstChild
        node_parent = html_node.parentNode
        
        # FIXME: remove sup without it's Child node
        #~ html_node.parentNode.appendChild(html_node.firstChild)
        html_node.parentNode.insertBefore(html_node.firstChild, html_node)
        html_node.parentNode.removeChild(html_node)

# Some Elements should be transfermed before others (like footnotes) by using OrderedDict.
transform_map = OrderedDict([
    ('sup', {
        'replace_with': 'transform_sup',
    }),
    
    ('div', {
        'replace_with': transform_ol,
    }),
    ('ol', {
        'replace_with': 'text:list',
        'attributes': {
            'xml:id': 'list' + str(randint(100000000000000000,900000000000000000))
        }
    }),
	
    ('a', {
		'replace_with': 'text:a',
		'attributes': {
			'xlink:type': 'simple',
			'xlink:href': ''
		}
	}),

    ('p', common_styles['p']),
    ('strong', common_styles['strong']),
    ('em', common_styles['italic']),
    ('b', common_styles['strong']),
    ('i', common_styles['italic']),

    # Heading Styles (Use styles defined in the document)
    ('h1', {
        'replace_with': 'text:p',
        'style_attributes': {
            'style-name': 'Heading_20_1'
        }
    }),

    ('h2', {
        'replace_with': 'text:p',
        'style_attributes': {
            'style-name': 'Heading_20_2'
        }
    }),

    ('h3', {
        'replace_with': 'text:p',
        'style_attributes': {
            'style-name': 'Heading_20_3'
        }
    }),

    ('h4', {
        'replace_with': 'text:p',
        'style_attributes': {
            'style-name': 'Heading_20_4'
        }
    }),

    ('pre', {
        'replace_with': 'text:p',
        'style_attributes': {
            'style-name': 'Preformatted_20_Text'
        }
    }),

    ('code', {
        'replace_with': 'text:span',
        'style_attributes': {
            'style-name': 'Preformatted_20_Text'
        }
    }),

    ('ul', {
        'replace_with': 'text:list',
        'attributes': {
            'xml:id': 'list' + str(randint(100000000000000000,900000000000000000))
        }
    }),

    ('li', {
        'replace_with': 'text:list-item'
    }),
    
    ('img', {
        'replace_with': transform_img
    })
])
