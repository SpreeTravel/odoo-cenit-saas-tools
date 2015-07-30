# -*- coding: utf-8 -*-
{
    'name': "Cenit SaaS web",

    'summary': "CenitSaaS.com specifics for web",

    'description': """
This module provides integration with cenitsaas.com as client
    """,

    'author': "OpenJAF",
    'website': "http://www.openjaf.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['web', 'cenit_saas_client'],
    'auto_install': True,

    # always loaded
    'data': [
        #~ 'security/rules.xml',
        #~ 'data.xml',
        'templates.xml',
    ],
    # only loaded in demonstration mode
    #~ 'demo': [
        #~ 'demo.xml',
    #~ ],
}
