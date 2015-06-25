# -*- coding: utf-8 -*-
{
    'name': "doorkeeper_oauth",

    'summary': "Doorkeeper-specific OAuth2 flow",

    'description': """
This module provides integration with Doorkeeper-specific authorization flows.
    """,

    'author': "Cenit",
    'website': "http://www.cenitsaas.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'auth_oauth'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data.xml',
        'templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
