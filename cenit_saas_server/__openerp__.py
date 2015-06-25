# -*- coding: utf-8 -*-
{
    'name': "Cenit SaaS server",

    'summary': "CenitSaaS.com specifics for servers",

    'description': """
This module provides integration with cenitsaas.com as server
    """,

    'author': "OpenJAF",
    'website': "http://www.openjaf.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'saas_server', 'doorkeeper_oauth'],

    # always loaded
    'data': [
        'auth_oauth_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #~ 'demo.xml',
    ],
}
