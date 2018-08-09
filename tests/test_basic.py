# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from xml.dom.minidom import getDOMImplementation
from unittest import TestCase
from secretary import UndefinedSilently, Renderer

def test_undefined_silently():
    undefined = UndefinedSilently()

    assert isinstance(undefined(), UndefinedSilently)
    assert isinstance(undefined.attribute, UndefinedSilently)
    assert str(undefined) == ''


class RendererTestCase(TestCase):
    def test_engine_build(self):
        engine = Renderer()

    def test_default_filters_registration(self):
        engine = Renderer()
        assert 'image' in engine.environment.filters, 'Image filter not present'
        assert 'markdown' in engine.environment.filters, 'Markdown filter not present'
        assert 'pad' in engine.environment.filters, 'Pad filter not present'
