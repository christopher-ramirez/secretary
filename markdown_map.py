#!/usr/bin/python

# Transform map used by the markdown filter. transform_map have
# instructions of how to transform a HTML style tag into a ODT document
# styled tag. Some ODT tags may need extra attributes; these are defined
# as a dict in the 'attributes' key. Also, some tags may need to create
# new styles in the document.

transform_map = {
    'p': { 
        'replace_with': 'text:p',
        'attributes': {
            'style-name': 'Standard'
        }
    },

    'strong': {
        'replace_with': 'text:span',
        'attributes': {
            'style-name': 'markdown_bold'
        },

        'append_style': {
            'name': 'markdown_bold',
            'properties': {
                'fo:font-weight': 'bold',
                'style:font-weight-asian': 'bold',
                'style:font-weight-complex': 'bold'
            }
        }
    },

    'i': {
        'replace_with': 'text:span',
        'attributes': {
            'style-name': 'markdown_italic'
        },

        'append_style': {
            'name': 'markdown_italic',
            'properties': {
                'fo:font-style': 'italic',
                'style:font-style-asian': 'italic',
                'style:font-style-complex': 'italic'
            }
        }
    },

    # Heading Styles (Use styles defined in the document)
    'h1': {
        'replace_with': 'text:p',
        'attributes': {
            'style-name': 'Heading_20_1'
        }
    },

    'h2': {
        'replace_with': 'text:p',
        'attributes': {
            'style-name': 'Heading_20_2'
        }
    },

    'h3': {
        'replace_with': 'text:p',
        'attributes': {
            'style-name': 'Heading_20_3'
        }
    },

    'h4': {
        'replace_with': 'text:p',
        'attributes': {
            'style-name': 'Heading_20_4'
        }
    },
    
}