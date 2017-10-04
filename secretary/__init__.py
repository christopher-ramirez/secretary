'''
Secretary
    This project is a document creation engine which uses LibreOffice documents
    as templates and makes use jinja2 to control variable printing and control
    flow.

    To render a template:
        engine = Renderer()
        result = engine.render(template_file, var1='foo', var2='bar')

    Copyright (c) 2012-2017 By:
        * Christopher Ramirez <chris.ramirezg@gmail.com>
        * Andres Reyes Monge (github.com/armonge)
        * Anton Kochnev (github.com/ak04nv)
        * DieterBuys (github.com/DieterBuys)

    Licensed under the MIT license.
'''

from __future__ import unicode_literals, print_function

import io
import re
import sys
import logging
import zipfile
from os import path
from mimetypes import guess_type, guess_extension
from uuid import uuid4
from jinja2 import Environment, Undefined, Markup, evalcontextfilter

from filters import RendererFilterInterface
from renders.odtrender import ODTRender, FlatODTRender

try:
    if sys.version_info.major == 3:
        xrange = range
        basestring = (str, bytes)
except AttributeError:
    # On Python 2.6 sys.version_info is a tuple
    if not isinstance(sys.version_info, tuple):
        raise


class SecretaryError(Exception):
    pass


class UndefinedSilently(Undefined):
    # Silently undefined,
    # see http://stackoverflow.com/questions/6182498
    def silently_undefined(*args, **kwargs):
        return ''

    return_new = lambda *args, **kwargs: UndefinedSilently()

    __unicode__ = silently_undefined
    __str__ = silently_undefined
    __call__ = return_new
    __getattr__ = return_new


class MediaInterface(object):
    '''Provides media handling capabilities to the Renderer class.'''

    def __init__(self, **kwargs):
        self.media_path = kwargs.pop('media_path', '')
        self.media_callback = self.fs_loader

    def media_loader(self, callback):
        '''
        Used as decorator. Sets media_loader property to the Render instance

        This sets the the media loader callback. A user defined function which
        handles the media loading. The function should take a template value,
        optionals args and kwargs. If media exists, it should returns a tuple
        whose first value if a file object type representing the media and
        optionally its second value is the media mimetype.

        Example:
            engine = Renderer()
            @engine.media_loader
            def picture_loader_from_db(pic_id):
                picture = db.picturec.findById(picId)
                return (picture.content, picture.mimetype)
        '''
        self.media_callback = callback
        return callback

    def fs_loader(self, media, *args, **kwargs):
        '''Loads a file from the file system.

        This is the default media loader in a Secretary Renderer instance.
        When media is a string value representing a file path, Here we load
        the file from the file system and returns its content and mime.

        media, can also be a stream with the content of the media.

        Args:
            media: A stream object or a relative or absolute path of a file.
                When it's a relative path, we use Renderer.media_path property
                to resolve the absolute path.

        Returns: A tuple with a stream object and mimetype of the media.
        '''
        if hasattr(media, 'seek') and hasattr(media, 'read'):
            return (media, 'image/jpeg')
        elif path.isfile(media):
            filename = media
        else:
            if not self.media_path:
                self.log.debug(
                    'media_path property not specified to load images from.')
                return

            filename = path.join(self.media_path, media)
            if not path.isfile(filename):
                self.log.debug('Media file "%s" does not exists.' % filename)
                return

        mime = guess_type(filename)
        return (open(filename, 'rb'), mime[0] if mime else None)


class Renderer(RendererFilterInterface, MediaInterface):
    '''
    Main engine to convert an ODT document into a jinja
    compatible template.

    Basic use example:
        engine = Renderer()
        result = engine.render(template, var1=val1, var2=val2, ...)


    Renderer provides an environment property which should be used
    to add custom filters to the ODF render.
        engine = Renderer()
        engine.environment.filters['custom_filter'] = filterFn
        result = engine.render('template.odt', var1=val1, ...)
    '''

    def __init__(self, environment=None, **kwargs):
        '''
        Create a Renderer instance.

        args:
            environment: Use this jinja2 environment. If not specified, we
                         create a new environment for this class instance.
        '''
        self.log = logging.getLogger(__name__)

        self.environment = environment or self.build_environment()

        super(Renderer, self).__init__(**kwargs)


    def build_environment(self):
        '''
        Builds and returns a new Jinja2 Environment instance suitable
        for use with Secretary.
        '''
        environment = Environment(
            undefined=UndefinedSilently,
            autoescape=True,
            finalize=self.finalize_value
        )

        # Setup some globals
        environment.globals['SafeValue'] = Markup

        return environment


    @evalcontextfilter
    def finalize_value(self, value, *args):
        """Escapes variables values."""
        if isinstance(value, Markup):
            return value

        return Markup(self.get_escaped_var_value(value))


    @staticmethod
    def get_escaped_var_value(value):
        """
        Encodes XML reserved chars in value (&, <, >) and also replaces
        the control chars \n and \t control chars to their ODF counterparts.
        """
        value = Markup.escape(value)
        return (
            value.replace('\n', Markup('<text:line-break/>'))
                 .replace('\t', Markup('<text:tab/>'))
                 .replace('\x0b', '<text:space/>')
                 .replace('\x0c', '<text:space/>')
        )


    def render(self, template, **kwargs):
        '''
        Render a template a ODT Template

        args:
            template: A template file. A file instance
            **kwargs: Template variables. Similar to jinja2

        returns:
            A binary stream which contains the rendered document.
        '''
        if hasattr(template, 'name') and template.name.endswith('.fodt'):
            return self.render_flat_odt(template, **kwargs)

        render_job = ODTRender(self, template, **kwargs)
        return render_job.render()

    def render_flat_odt(self, template, **kwargs):
        '''
        Render a template a Flat ODT template

        args:
            template: A template file. A file instance
            **kwargs: Template variables. Similar to jinja2

        returns:
            A binary stream which contains the rendered document.
        '''
        render_job = FlatODTRender(self, template, **kwargs)
        return render_job.render()
