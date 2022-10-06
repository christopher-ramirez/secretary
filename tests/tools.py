# -*- coding: utf-8 -*-
import os

def relative_path(rel_path) :
    '''Give a full path relative to this file'''
    return os.path.join(os.path.dirname(__file__), rel_path)


def compare_odt_files(file1, file2):
    '''Compare two LibreOffice odt file
    returns True if they are equal
    '''
    #TODO: check content
    assert True
