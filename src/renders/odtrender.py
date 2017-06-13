import sys
import logging
import zipfile
import base64
from io import BytesIO
from os import path
from xml.dom.minidom import parseString
from mimetypes import guess_type, guess_extension

from base import Job

class ODTRender(Job):
    archive = None
    def render(self):
        """Implements rendering of ODT files."""
        logging.debug('Starting template rendering job')
        self._unpack()
        self._before_job_start()
        self.manifest = parseString(self.archive.read('META-INF/manifest.xml'))

        # render all *.xml files that can be found inside the archive
        map(lambda zip_file: self.render_archive_xml(zip_file),
            filter(lambda f: f.endswith('.xml'), self.files.keys()))

        self._after_job_end()
        return self._pack().getvalue()

    def render_archive_xml(self, filename):
        """Receives a ZipInfo archive file holding a XML and renders its contents."""
        xml_source = self.archive.read(filename)
        if not xml_source:
            return

        final_xml = self.render_xml(xml_source)
        self.files[filename] = final_xml

    def add_document_media(self, reference_node, media, **kwargs):
        """Adds a media to archive."""
        final_path = self._add_media_to_archive(media, kwargs.get('mimetype', ''))
        reference_node.setAttribute('xlink:href', final_path)

    def _add_media_to_archive(self, media, mimetype='', name=''):
        extension = None
        if hasattr(media, 'name') and not name:
            name, extension = path.splitext(media.name)

        if not extension:
            extension = guess_extension(mimetype)

        media_path = 'Pictures/{0}{1}'.format(name, extension)
        media.seek(0)
        self.files[media_path] = media.read(-1)
        if hasattr(media, 'close'):
            media.close()

        self._register_in_manifest(media_path, mimetype)
        return media_path

    def _register_in_manifest(self, media_path, mimetype=''):
        '''Register into archive manifest.xml a media added to archive.'''
        manifests = self.manifest.getElementsByTagName('manifest:manifest')[0]
        media_node = self.manifest.createElement('manifest:file-entry')
        manifests.appendChild(media_node)
        media_node.setAttribute('manifest:full-path', media_path)
        media_node.setAttribute('manifest:media-type', mimetype)

    def _unpack(self):
        # Unpack this job's templates and load every file in it into self.files
        logging.debug('Unpacking template')
        self.archive = zipfile.ZipFile(self.template, 'r')
        for zf in self.archive.filelist:
            self.files[zf.filename] = self.archive.read(zf.filename)

    def _pack(self):
        # Packs and return this Job ODT archive
        output_stream = BytesIO()
        zip_file = zipfile.ZipFile(output_stream, 'a')
        for name, content in self.files.items():
            # exclude manifest, it will be added at the end
            if name == 'META-INF/manifest.xml':
                continue

            if sys.version_info >= (2, 7):
                zip_file.writestr(name, content, zipfile.ZIP_DEFLATED)
            else:
                zip_file.writestr(name, content)

        # Finally, write manifest version kept by this class
        zip_file.writestr('META-INF/manifest.xml', self.manifest.toxml().encode('ascii'))

        return output_stream

class FlatODTRender(Job):
    '''
    Implements rendering of Flat ODT files.
    '''
    def render(self):
        xml_source = self.template.read(-1)

        if not xml_source:
            return None

        final_xml = self.render_xml(xml_source)
        return final_xml

    def add_document_media(self, reference_node, media, **kwargs):
        xml = kwargs.pop('xml')
        base64_content = xml.createTextNode(base64.encodestring(media.read(-1)))
        base64_node = xml.createElement('office:binary-data')
        base64_node.appendChild(base64_content)

        current_binary_data = None
        for child in reference_node.childNodes:
            if child.nodeName == 'office:binary-data':
                current_binary_data = child

        if current_binary_data:
            reference_node.replaceChild(base64_node, current_binary_data)
        else:
            reference_node.appendChild(base64_node)
