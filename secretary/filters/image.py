'''
    Implements Secretary's "image" filter.
'''

from uuid import uuid4
from .base import SecretaryFilterInterface


class ImageFilter(SecretaryFilterInterface):
    '''Image filter implementation'''

    def render(self, value, *args, **kwargs):
        '''
        Returns a placeholder value identifying **value** and params received.
        When the engine finishes rendering the current XML document, replace the
        placeholder values returned here with the final images retrived throught
        renderer.media_callback function.
        '''
        placeholder_value = uuid4().hex
        self.placeholders[placeholder_value] = {
            'value': value,
            'args': args,
            'kwargs': kwargs
        }
        return placeholder_value

    def before_render_xml(self, renderer, job, xml):
        self.placeholders = dict()

    def after_render_xml(self, renderer, job, xml):
        if len(self.placeholders.keys()):
            self.replace_images(job, xml)

        self.placeholders = None

    def replace_images(self, job, xml):
        '''
        Replaces placeholder values with content retrieved with callback_media.
        '''
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
            for name, value in frame_attrs.items():
                draw_frame.setAttribute(name, value)

            for name, value in image_attrs.items():
                draw_image.setAttribute(name, value)

            # TODO: Decide if to keep original `value` string.

            if not media[0]:
                continue

            job.add_document_media(draw_image, media[0], mimetype=media[1],
                                   name=placeholder_value, xml=xml)

    def _frame_and_image_attrs(self, draw_frame):
        '''
        Returns a tuple of two dictionaries. The first contains the XML
        attributes of draw:frame node. The second contains the attributes of
        "draw:image" node (child of draw:frame).
        '''
        frame_attrs = dict()
        for attr_index in range(draw_frame.attributes.length):
            attr = draw_frame.attributes.item(attr_index)
            frame_attrs.update({attr.name: attr.value})

        # Extract draw:image attributes
        draw_image = draw_frame.childNodes[0]
        image_attrs = dict()
        for attr_index in range(draw_image.attributes.length):
            attr = draw_image.attributes.item(attr_index)
            image_attrs.update({attr.name: attr.value})

        return (frame_attrs, image_attrs)

    @staticmethod
    def draw_frames(xml):
        '''
        Generator returning all draw:frame elements found in xml
        '''
        for frame in xml.getElementsByTagName('draw:frame'):
            if not frame.hasChildNodes():
                continue

            yield frame
