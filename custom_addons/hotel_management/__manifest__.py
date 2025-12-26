{
    'name': 'Quản lý Khách sạn',
    'version': '1.0',
    'summary': 'Hotel Management System',
    'category': 'Tools',
    'author': 'You',
    'depends': ['base'],
    'data': [
        'security/hotel_security.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'views/views.xml',
    ],
    'installable': True,
    'application': True,
}
