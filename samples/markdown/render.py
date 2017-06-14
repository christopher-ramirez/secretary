import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(__file__, '../../../src')))

from __init__ import Renderer

if __name__ == '__main__':
    engine = Renderer()
    template = open('template.fodt', 'rb')
    output = open('output.fodt', 'wb')

    output.write(engine.render(template))
    print("Template rendering finished! Check output.fodt file.")
