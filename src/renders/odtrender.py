import sys
import logging
import zipfile
from io import BytesIO

from base import Job

class ODTRender(Job):
    archive = None
    def render(self):
        logging.debug('Starting template rendering job')
        self._unpack()
        self._before_job_start()

        # render all *.xml files that can be found inside the archive
        map(lambda zip_file: self.render_zip_file(zip_file),
            filter(lambda f: f.filename.endswith('.xml'), self.files.keys()))

        self._after_job_end()
        return self._pack().getvalue()

    def render_zip_file(self, zip_file):
        xml_source = self.archive.read(zip_file.filename)
        if not xml_source:
            return

        final_xml = self.render_xml(xml_source)
        self.files[zip_file] = final_xml

    def _unpack(self):
        # Unpack this job's templates and load every file in it into self.files
        logging.debug('Unpacking template')
        self.archive = zipfile.ZipFile(self.template, 'r')
        for f in self.archive.filelist:
            self.files[f] = self.archive.read(f)

    def _pack(self):
        # Packs and return this Job ODT archive
        output_stream = BytesIO()
        zip_file = zipfile.ZipFile(output_stream, 'a')
        for name, content in self.files.items():
            if sys.version_info >= (2, 7):
                zip_file.writestr(name, content, zipfile.ZIP_DEFLATED)
            else:
                zip_file.writestr(name, content)

        return output_stream
