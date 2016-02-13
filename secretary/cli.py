import os
import logging
import argparse
from datetime import datetime

from .secretary import Renderer
from .utils import logger


def secretary_init(input, output=None, template=None):
    logger.info('Secretary Initialized')

    root = os.path.dirname(input)

    if not root:
        root = os.getcwd()
    if not os.path.isabs(root):
        root = os.path.abspath(root)

    if not output:
        output = 'output.odt'
    if not os.path.isabs(output):
        output = os.path.join(root, output)
    if not output.endswith('.odt'):
        output = '%s.odt' % output

    if not template:
        template = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template.odt')

    document = {
        'markdown': open(input, 'r').read(),
        'datetime': datetime.now()
    }

    engine = Renderer(media_path=root, markdown_extras=['fenced-code-blocks',
                                                        'footnotes',
                                                        'tables'])
    result = engine.render(template, document=document)
    with open(output, 'wb') as f:
        f.write(result)
    logger.info('Secretary Finished, please open %s' % output)


def main():
    parser = argparse.ArgumentParser(description='Secretary')
    parser.add_argument('input',
                        help='Markdown Formatted File')
    parser.add_argument('-o', '--output',
                        default='output.odt',
                        help='ODT output file')
    parser.add_argument('-t', '--template',
                        help='ODT template file')

    parser.add_argument('-v', '--verbose',
                        action='count',
                        help='Be verbose')

    args = parser.parse_args()
    if args.verbose:
        verbosity_levels = [logging.INFO, logging.DEBUG]
        verbosity_level = args.verbose - 1
        logging.basicConfig(level=verbosity_levels[verbosity_level])
        logger.setLevel(verbosity_levels[verbosity_level])

    secretary_init(input=args.input, output=args.output, template=args.template)
