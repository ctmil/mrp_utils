{
    'name': 'MRP - Tools',
    'version': '13.0.1.0.0',
    'author': 'Moldeo Interactive',
    'category': 'Sales',
    'sequence': 14,
    'license': 'AGPL-3',
    'summary': '',
    'depends': [
        'mrp',
        'mail',
        'utm',
    ],
    'data': [
        'ogc_mrp_view.xml',
        'wizard/wizard_view.xml',
        'security/ir.model.access.csv'
        ],
    'installable': True,
    'auto_install': False,
}
