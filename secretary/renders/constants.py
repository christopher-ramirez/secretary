"""
    Define some constant values and objects
"""


FLOW_REFERENCES = {
    'text:p'             : 'text:p',
    'paragraph'          : 'text:p',
    'before::paragraph'  : 'text:p',
    'after::paragraph'   : 'text:p',

    'table:table-row'    : 'table:table-row',
    'table-row'          : 'table:table-row',
    'row'                : 'table:table-row',
    'before::table-row'  : 'table:table-row',
    'after::table-row'   : 'table:table-row',
    'before::row'        : 'table:table-row',
    'after::row'         : 'table:table-row',

    'table:table-cell'   : 'table:table-cell',
    'table-cell'         : 'table:table-cell',
    'cell'               : 'table:table-cell',
    'before::table-cell' : 'table:table-cell',
    'after::table-cell'  : 'table:table-cell',
    'before::cell'       : 'table:table-cell',
    'after::cell'        : 'table:table-cell',
}
