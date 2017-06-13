import logging
from uuid import uuid4


class ImageFilter(object):
    def __init__(self, renderer):
        self.renderer = renderer
        renderer.register_before_xml_render(self._before_render_xml)
        renderer.register_after_xml_render(self._after_render_xml)

    def render(self, value, *args, **kwargs):
        '''
        Filter implementation. Returns an unique value identifying value received.
        When the engine finishes rendering the current XML document, replace the
        unique values generated here with the final images retrived throught
        renderer.media_callback function.
        '''
        placeholder_value = uuid4().hex
        self.placeholders[placeholder_value] = {
            'value': value,
            'args': args,
            'kwargs': kwargs
        }
        return placeholder_value

    def _before_render_xml(self, renderer, job, xml):
        self.placeholders = dict()

    def _after_render_xml(self, renderer, job, xml):
        if len(self.placeholders.keys()):
            self._replace_images(job, xml)

        self.placeholders = None

    def _replace_images(self, job, xml):
        for draw_frame in self.draw_frames(xml):
            placeholder_value = draw_frame.getAttribute('draw:name')
            if not placeholder_value in self.placeholders:
                continue

            # Keep draw:frame attributes in frame_attrs dictionary
            draw_image = draw_frame.childNodes[0]
            frame_attrs, image_attrs = self._frame_and_image_attrs(draw_frame)

            # Request to media loader the image media to use
            mc_data = self.placeholders[placeholder_value]
            media = self.renderer.media_callback(
                mc_data['value'], *mc_data['args'], frame_attrs=frame_attrs,
                image_attrs=image_attrs, **mc_data['kwargs']
            )

            # update draw_frame and image_frame if they were updated in media_callback
            map(lambda (k, v): draw_frame.setAttribute(k, v), frame_attrs.items())
            map(lambda (k, v): draw_image.setAttribute(k, v), image_attrs.items())

            # TODO: Decide if to keep original `value` string.

            if not media[0]:
                continue

            job.add_document_media(draw_image, media[0], mimetype=media[1],
                                   name=placeholder_value, xml=xml)

    def _frame_and_image_attrs(self, draw_frame):
        '''Returns a tuple of two dictionaries. The first contains the
        XML attributes of draw_frame. The second contains the XML
        attributes of draw:image node (child of draw:frame).'''
        frame_attrs = dict()
        map(lambda a: frame_attrs.update({a.name: a.value}),
            [draw_frame.attributes.item(i) for i in xrange(draw_frame.attributes.length)])

        # Extract draw:image attributes
        draw_image = draw_frame.childNodes[0]
        image_attrs = dict()
        map(lambda a: image_attrs.update({a.name: a.value}),
            [draw_image.attributes.item(i) for i in xrange(draw_image.attributes.length)])

        return (frame_attrs, image_attrs)

    @staticmethod
    def draw_frames(xml):
        '''Returns a generator returning draw:frame elements in xml'''
        for frame in xml.getElementsByTagName('draw:frame'):
            if not frame.hasChildNodes():
                continue

            yield frame
