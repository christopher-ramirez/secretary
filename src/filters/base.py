class SecretaryFilterInterface(object):
    '''Base interface for a Secretary filters.

    The advantage of Secretary filters over the simple python function ones is
    that Secretary filters can perform work before and after a document redering
    happends. This allows the filter to make pre and post processing.
    '''

    def __init__(self, renderer):
        self.renderer = renderer
        renderer.register_for_job_start(self.on_start_job)
        renderer.register_for_job_end(self.on_end_job)
        renderer.register_before_xml_render(self.before_render_xml)
        renderer.register_after_xml_render(self.after_render_xml)

    def on_start_job(self, renderer, job):
        '''Called when a render job is about to start.'''
        pass

    def on_end_job(self, renderer, job):
        '''Called when a render job ends.'''
        pass

    def before_render_xml(self, renderer, job, xml):
        '''Called before a xml is rendered as part of document creation job.'''
        pass

    def after_render_xml(self, renderer, job, xml):
        '''Called after a xml is rendered as part of document creation job.'''
        pass
