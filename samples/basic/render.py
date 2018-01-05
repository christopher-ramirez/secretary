#!/usr/bin/env python

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(__file__, '../../..')))

from secretary import Renderer


def main():
    countries = [
        {'country': 'United States', 'capital': 'Washington', 'cities': [
            'miami', 'new york', 'california', 'texas', 'atlanta']},
        {'country': 'England', 'capital': 'London', 'cities': ['gales']},
        {'country': 'Japan', 'capital': 'Tokio',
            'cities': ['hiroshima', 'nagazaki']},
        {'country': 'Nicaragua', 'capital': 'Managua',
            'cities': ['leon', 'granada', 'masaya']},
        {'country': 'Argentina', 'capital': 'Buenos aires'},
        {'country': 'Chile', 'capital': 'Santiago'},
        {'country': 'Mexico', 'capital': 'MExico City',
            'cities': ['puebla', 'cancun']},
    ]

    engine = Renderer()
    template = open('template.fodt', 'rb')
    output = open('output.fodt', 'wb')

    output.write(engine.render(template, countries=countries))

    print("Template rendering finished! Check output.fodt file.")


if __name__ == "__main__":
    main()
