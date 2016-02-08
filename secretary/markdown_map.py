#!/usr/bin/python

from random import randint

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

transform_map = {
	'a': {
		'replace_with': 'text:a',
		'attributes': {
			'xlink:type': 'simple',
			'xlink:href': ''
		}
	},

    'p': common_styles['p'],
    'strong': common_styles['strong'],
    'em': common_styles['italic'],
    'b': common_styles['strong'],
    'i': common_styles['italic'],

    # Heading Styles (Use styles defined in the document)
    'h1': {
        'replace_with': 'text:p',
        'style_attributes': {
            'style-name': 'Heading_20_1'
        }
    },

    'h2': {
        'replace_with': 'text:p',
        'style_attributes': {
            'style-name': 'Heading_20_2'
        }
    },

    'h3': {
        'replace_with': 'text:p',
        'style_attributes': {
            'style-name': 'Heading_20_3'
        }
    },

    'h4': {
        'replace_with': 'text:p',
        'style_attributes': {
            'style-name': 'Heading_20_4'
        }
    },

    'pre': {
        'replace_with': 'text:p',
        'style_attributes': {
            'style-name': 'Preformatted_20_Text'
        }
    },

    'code': {
        'replace_with': 'text:span',
        'style_attributes': {
            'style-name': 'Preformatted_20_Text'
        }
    },

    'ul': {
        'replace_with': 'text:list',
        'attributes': {
            'xml:id': 'list' + str(randint(100000000000000000,900000000000000000))
        }
    },

    'ol': {
        'replace_with': 'text:list',
        'attributes': {
            'xml:id': 'list' + str(randint(100000000000000000,900000000000000000))
        }
    },

    'li': {
        'replace_with': 'text:list-item'
    },
}