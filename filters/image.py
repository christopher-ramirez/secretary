import logging
from uuid import uuid4


class ImageFilter():
    def __init__(self, engine, **kwargs):
        self.engine = engine
        self.engine.environment.filters['image'] = self.filter
        engine.before_render_xml(self.before_render_starts)
        engine.after_render_xml(self.after_renders_end)

    def filter(self, value, *args, **kwargs):
        key = uuid4().hex
        self.images[key] = {
            'value': value,
            'args': args,
            'kwargs': kwargs
        }

        return key

    def before_render_starts(self, xml_document):
        self.images = dict()

    def after_renders_end(self, xml_document):
        if self.images:
            self.replace_images_in_xml(xml_document)

    def replace_images_in_xml(self, xml_doc):
        logging.info('Replacing images in final document')
        for image_frame in self.get_images_frames_in_document(xml_doc):
            frame_attrs = dict()
            for i in xrange(image_frame.attributes.length):
                attr = image_frame.attributes.item(i)
                frame_attrs[attr.name] = attr.value

            image_node = image_frame.childNodes[0]
            image_attrs = dict()
            for i in xrange(image_node.attributes.length):
                attr = image_node.attributes.item(i)
                image_attrs[attr.name] = attr.value

            key = image_frame.getAttribute('draw:name')
            image = self.engine.media_callback(self.images[key]['value'],
                                               *self.images[key]['args'],
                                               frame_attrs=frame_attrs,
                                               image_attrs=image_attrs,
                                               **self.images[key]['kwargs'])

            # update image frame and actual image node attrs
            # (if they where updated in media_callback)
            for k, v in frame_attrs.items():
                image_frame.setAttribute(k, v)

            for k, v in image_attrs.items():
                image_node.setAttribute(k, v)

            if isinstance(self.images[key]['value'], basestring):
                image_frame.setAttribute('draw:name', self.images[key]['value'])

            if image:
                mname = self.engine.add_media_to_archive(media=image[0],
                        mime=image[1], name='Pictures/{0}'.format(key))
                if mname:
                    image_node.setAttribute('xlink:href', mname)


    def get_images_frames_in_document(self, xml):
        frames = xml.getElementsByTagName('draw:frame')
        for frame in frames:
            if not frame.hasChildNodes():
                continue

            if frame.getAttribute('draw:name') not in self.images:
                continue

            yield frame
