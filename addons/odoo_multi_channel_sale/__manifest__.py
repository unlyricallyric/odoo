# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
    "name": "Odoo Multi-Channel Sale",
    "summary": """The multi channel module is Multiple platform connector with Odoo. You can connect and manage various platforms like Amazon, Bagisto, Cscart, CSV, Ebay, Etsy, Flipkart, Magento 2, Prestashop, Shopify, Walmart, Woocommerce in odoo with the help of Odoo multichannel sale bridge.""",
    "category": "Website",
    "version": "2.4.0",
    "sequence": 1,
    "author": "Webkul Software Pvt. Ltd.",
    "license": "Other proprietary",
    "website": "https://store.webkul.com/odoo-multi-channel-sale.html",
    "description": """Odoo multi-channel bridge
        Multi channel connector
        Multi platform connector
        Multiple platforms bridge
        Connect Amazon with odoo
        Amazon bridge
        Flipkart Bridge
        Magento Odoo Bridge
        Odoo magento bridge
        Woocommerce odoo bridge

        Odoo woocommerce bridge
        Ebay odoo bridge
        Odoo ebay bridge

        Multi channel bridge
        Prestashop odoo bridge
        Odoo prestahop
        Akeneo bridge
        Etsy bridge
        Marketplace bridge
        Multi marketplace connector
        Multiple marketplace platform""",
    "live_test_url": "https://apps.odoo.com/apps/modules/browse?repo_maintainer_id=120854&search=extensions%20for%20multichannel",
    "depends": [
        'delivery',
        'wk_wizard_messages',
    ],
    "data": [
        'security/security.xml',
        'security/ir.model.access.csv',

        'wizard/wizard_message_view.xml',
        'wizard/imports/import_operation.xml',
        'wizard/exports/export_operation.xml',

        'views/menus.xml',
        'views/base/channel_order_states.xml',
        'views/base/multi_channel_sale.xml',
        'views/core/product_category.xml',
        'views/core/product_template.xml',
        'views/core/product_product.xml',
        'views/core/product_pricelist.xml',
        'views/core/res_partner.xml',
        'views/core/sale_order.xml',
        'views/core/res_config.xml',
        'views/feeds/category_feed.xml',
        'views/feeds/order_feed.xml',
        'views/feeds/order_line_feed.xml',
        'views/feeds/partner_feed.xml',
        'views/feeds/product_feed.xml',
        'views/feeds/variant_feed.xml',
        'views/feeds/shipping_feed.xml',
        'views/mappings/channel_synchronization.xml',
        'views/mappings/account_journal_mapping.xml',
        'views/mappings/account_mapping.xml',
        'views/mappings/attribute_mapping.xml',
        'views/mappings/attribute_value_mapping.xml',
        'views/mappings/category_mapping.xml',
        'views/mappings/order_mapping.xml',
        'views/mappings/partner_mapping.xml',
        'views/mappings/pricelist_mapping.xml',
        'views/mappings/product_template_mapping.xml',
        'views/mappings/product_variant_mapping.xml',
        'views/mappings/shipping_mapping.xml',
        #  'views/template.xml',
        'wizard/exports/export_category.xml',
        'wizard/exports/export_product.xml',
        'wizard/exports/export_template.xml',
        'wizard/update_mapping_wizard.xml',
        'wizard/feed_wizard.xml',
        'data/evaluation_action.xml',
        'data/export_action.xml',
        'data/update_mapping_action.xml',
        'data/cron.xml',
        'data/data.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_multi_channel_sale/static/src/css/dashboard.css',
            'odoo_multi_channel_sale/static/src/js/dashboard.js',
            'odoo_multi_channel_sale/static/src/xml/multichannel_dashboard.xml',
            'odoo_multi_channel_sale/static/src/xml/instance_dashboard.xml',
        ],
        # 'web.assets_qweb': [
        #   'odoo_multi_channel_sale/static/src/xml/multichannel_dashboard.xml',
        #   'odoo_multi_channel_sale/static/src/xml/instance_dashboard.xml',
        # ],

    },
    "images": ['static/description/banner.gif'],
    "application": True,
    "installable": True,
    "auto_install": False,
    "price": 29,
    "currency": "USD",
    "pre_init_hook": "pre_init_check",
}
