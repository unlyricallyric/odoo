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
  "name"                 :  "Shopify Odoo Connector | Odoo Multichannel",
  "summary"              :  """Integrate Shopify marketplace with Odoo.
		Configure you Shopify store with Odoo. Manage orders, products, etc at Odoo's end. multi channel multi-channel shopify multichannel shopify bridge shopify connector shopify odoo bridge odoo shopify extensions for multichannel""",
  "category"             :  "Website",
  "version"              :  "1.1.18",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/odoo-multichannel-shopify-connector.html",
  "description"          :  """https://webkul.com/blog/odoo-multichannel-shopify-connector/
    Shopify Connector
		Shopify integration
		Shopify Odoo Bridge
		Shopify Integration
		Shopify integration
		Connect Shopify
		Connect Shopify
		Shopify bridge
		Shopify to Odoo
		Shopify to Odoo
		Manage orders
		Manage products
		Import products
		Import customers
		Import orders""",
  "live_test_url"        :  "http://odoodemo.webkul.com/demo_feedback?module=shopify_odoo_bridge",
  "depends"              :  ['odoo_multi_channel_sale'],
  "data"                 :  [
                             'views/multi_channel_sale.xml',
                             'wizard/import_operation.xml',
                             'wizard/export_category.xml',
                             'wizard/export_template.xml',
                             'data/data.xml',
                            ],
  'assets': {
    'web.assets_backend': [
      'shopify_odoo_bridge/static/src/xml/instance_dashboard.xml',
    ],
    },
  "images"               :  ['static/description/Banner.gif'],
  "application"          :  True,
  "price"                :  170.0,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}
