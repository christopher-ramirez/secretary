#!/usr/bin/env python

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(__file__, '../../..')))

from secretary import Renderer


def main():
    engine = Renderer()
    template = open('template.fodt', 'rb')
    output = open('output.fodt', 'wb')

    output.write(engine.render(template))
    print("Template rendering finished! Check output.fodt file.")


if __name__ == '__main__':
    main()
