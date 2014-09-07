# /usr/bin/activate

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(__file__, '../../..')))
    
from secretary import Renderer

if __name__ == '__main__':
    engine = Renderer(media_path='.')
    template = open('template.odt', 'rb')
    output = open('output.odt', 'wb')

    output.write(engine.render(template, image='writer.png'))
    print("Template rendering finished! Check output.odt file.")