# -*- coding: utf-8 -*-
{
    'name': "TerraLab",

    'summary': """
        TerraLab System""",

    'description': """
        TerraLab extends Odoo by adding laboratory management functions.
    """,

    'author': "TerraLab Oy",
    'website': "https://www.terralab.fi",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    # Fixed version syntax. Odoo add-ons versions scheme must be major odoo version.x.x.x for Odoo to detect changes in modules and apply updates. In this case 13.x.x.x.
    'category': 'Specific Industry Applications',
    'version': '13.0.2.20',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product', 'sale', 'google_spreadsheet', 'uom', 'mrp', 'stock', 'sale_management'],

    # always loaded; these need to be in a specific order
    'data': [
        'security/ir.model.access.csv',
        'data/sites.xml',
        'reports/terralab_offer.xml',
        'reports/terralab_order_confirmation.xml',
        'reports/terralab_test_results.xml',
        'reports/terralab_common_header.xml',
        'reports/terralab_common_footer.xml',
        'reports/terralab_common_css.xml',
        # Models
        'views/order_form.xml',
        'views/order_views.xml',
        'views/product_views.xml',
        'views/category_views.xml',
        'views/sample_type_views.xml',
        'views/spreadsheet_views.xml',
        'views/submitted_sample_views.xml',
        'views/submitted_test_views.xml',
        'views/submitted_test_variable_views.xml',
        'views/test_type_views.xml',
        'views/test_variable_type_views.xml',
        'views/target_use_type_views.xml',
        # Menu
        'views/menu_actions.xml',
        'views/menu_items.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,

    # PIP requirements - install with pip3 install google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib oauth2client
    'external_dependencies': {
        'python': ['google-api-python-client', 'google-auth', 'google-auth-httplib2', 'google-auth-oauthlib', 'oauth2client'],
    },
}
