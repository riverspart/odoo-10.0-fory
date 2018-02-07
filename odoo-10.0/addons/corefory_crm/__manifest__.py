# -*- coding: utf-8 -*-
{
    'name': 'Core fory CRM',
    'version': '1.0',
    'category': 'corefory',
    'description': """A module to verify the inheritance using _inherits.""",
    'author': 'tungnt.it',
    'website': 'http://www.tanhoangminh.com.vn',
    'depends': [
        'crm',
        'purchase'
    ],
    'data': [
        'security/corefory_crm_security.xml',
        'security/corefory_crm_loyalty_security.xml',
        'security/corefory_purchase_request.xml',
        'security/ir.model.access.csv',
        'data/corefory_crm_data.xml',
        'views/res_partner_view.xml',
        'views/crm_lead_view.xml',
        'views/stock_picking_view.xml',
        'views/make_procurement_views.xml',
        'views/corefory_purchase_request_view.xml',
        'views/corefory_loyalty_card_view.xml',
        'views/corefory_coupon_view.xml',
        'views/corefory_loyalty_card_config.xml',
        'views/corefory_loyalty_card_type_view.xml',
        'views/sale_order_view.xml',
        'views/pos_order_view.xml',
        'views/stock_quant_view.xml',
        'views/corefory_crm_templates.xml',
        'report/stock_report_views.xml',
        'views/corefory_product_slider_view.xml',
        'views/corefory_product_brand_view.xml',
        # 'report/report_saledetails.xml',
        'report/report_stockpicking_operations.xml',
        'views/product_template_view.xml',
        'views/corefory_product_supplierinfo_import.xml',

    ],
    'qweb': [
        'static/src/xml/pos_extend.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
