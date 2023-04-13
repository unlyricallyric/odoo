# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
import binascii
import logging
import requests
import pytz
import json
from odoo.tools.safe_eval import dateutil
from datetime import date
from dateutil import parser
from odoo import fields, models, api, _
from ...tools import ReverseDict
_logger = logging.getLogger(__name__)

AUTH_USER_NAME = "DigitalStarAPI"
AUTH_PASSWORD = "r@4?J]p8PgB6XZLv"
API_DOMAIN_URL = "http://dsecomapinetcore-test.us-east-1.elasticbeanstalk.com/api"

HelpImportOrderDate = _(
    """A date used for selecting orders created after (or at) a specified time."""
)

HelpUpdateOrderDate = _(
    """
    A date used for selecting orders that were last updated after (or at) a specified time.
     An update is defined as any change in order status,includes updates made by the seller.
"""
)
DefaultStore = _("""***While using multi store***\n
Select the default store/parent store
from where the order and partner will imported for this child store.
""")

STATE = [
    ('draft', 'Draft'),
    ('validate', 'Validate'),
    ('error', 'Error')
]
DEBUG = [
    ('enable', 'Enable'),
    ('disable', 'Disable')
]
ENVIRONMENT = [
    ('production', 'Production Server'),
    ('sandbox', 'Testing(Sandbox) Server)')
]
FEED = [
    ('all', 'For All Models'),
    ('order', 'For Order Only'),
]

MAPPINGMODEL = {
    'product.product': 'channel.product.mappings',
    'product.template': 'channel.template.mappings',
    'res.partner': 'channel.partner.mappings',
    'product.category': 'channel.category.mappings',
    'sale.order': 'channel.order.mappings',
}
TaxType = [
    ('include', 'Include In Price'),
    ('exclude', 'Exclude In Price')
]

METAMAP = {
    'product.category': {
        'mapping': 'channel.category.mappings',
        'local_field': 'odoo_category_id',
        'channel_field': 'store_category_id',
        'feed': 'category.feed'
    },
    'product.template': {
        'mapping': 'channel.template.mappings',
        'local_field': 'odoo_template_id',
        'channel_field': 'store_product_id',
        'feed': 'product.feed'
    },
    'product.product': {
        'mapping': 'channel.product.mappings',
        'local_field': 'erp_product_id',
        'channel_field': 'store_variant_id'
    }
}


class MultiChannelSale(models.Model):
    _name = 'multi.channel.sale'
    _description = 'Multi Channel Sale'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    import_order_cron = fields.Boolean("Import Orders")
    import_product_cron = fields.Boolean("Import Products")
    import_partner_cron = fields.Boolean("Import Customers")
    import_category_cron = fields.Boolean("Import Categories")

    channel_stock_action = fields.Selection([
        ('qoh', 'Quantity on hand'),
        ('fq', 'Forecast Quantity')
    ],
        default='qoh',
        string='Stock Management',
        help="Manage Stock")

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if 'install_mode' in self._context or 'create_order_states' in self._context:
            res._on_change_channel()
        channels = self.get_core_feature_compatible_channels()
        return res

    url = fields.Char("URL")
    email = fields.Char(string='Api User')
    api_key = fields.Char("Password")

    def test_connection(self):
        # for commerceHub connector
        if self.channel == 'commerceHub':
            payload = {
                "status": "any",
                "apiKey": self.email,
                "apiSecret": self.api_key
            }
            url = API_DOMAIN_URL + "/testConnection"
            response = requests.get(url, auth=(AUTH_USER_NAME, AUTH_PASSWORD), params=payload)
            if response.status_code == 200:
                print("############# response code is ################")
                print(response.status_code)
                self.state = 'validate'
            return self.display_message('Connection has been successfully established!')
        
        self.ensure_one()
        if hasattr(self, 'connect_%s' % self.channel):
            res, msg = getattr(self, 'connect_%s' % self.channel)()
            print(res)
            print(msg)
            self.state = 'validate' if res else 'error'
            return self.display_message(msg)
        elif hasattr(self, 'test_%s_connection' % self.channel):
            _logger.warning(
                'Error in use of MultiChannelSale class: '
                'use of test_connection function to establish connection to Channel.'
            )
            return getattr(self, 'test_%s_connection' % self.channel)()
        else:
            return self.display_message('Connection protocol missing.')
        

    @api.onchange('channel')
    def _on_change_channel(self):
        if self.channel:
            if self.order_state_ids:
                rec = self.env['channel.order.states'].search([('channel_id', '=', self._origin.id), ('channel_name', '=', self.channel)])

                if rec:
                    self.order_state_ids = [(6, 0, rec.ids)]
                else:
                    self.order_state_ids = [(5, 0, 0)]
                    if hasattr(self, '%s_default_order_state' % self.channel):
                        """
                        Add default values to order state ids
                        @field channel_state: state of the channel
                        @field default_order_state: True or False
                        @field odoo_create_invoice: True or False
                        @field odoo_ship_order: True or False
                        @field odoo_order_state: draft or shipped or done etc.
                        @field odoo_set_invoice_state: paid or open
                        @return: A list dictionarys of the default values
                        """
                        values = getattr(self, '%s_default_order_state' % self.channel)()
                        rec_val = []
                        for rec in values:
                            rec_val.append((0, 0, rec))
                        self.order_state_ids = rec_val
            else:
                if hasattr(self, '%s_default_order_state' % self.channel):
                    """
                    Add default values to order state ids
                    @field channel_state: state of the channel
                    @field default_order_state: True or False
                    @field odoo_create_invoice: True or False
                    @field odoo_ship_order: True or False
                    @field odoo_order_state: draft or shipped or done etc.
                    @field odoo_set_invoice_state: paid or open
                    @return: A list dictionarys of the default values
                    """
                    values = getattr(self, '%s_default_order_state' % self.channel)()
                    rec_val = []
                    for rec in values:
                        rec_val.append((0, 0, rec))
                    self.order_state_ids = rec_val

    def set_to_draft(self):
        self.state = 'draft'

    def open_mapping_view(self):
        self.ensure_one()
        res_model = self._context.get('mapping_model')
        mapping_ids = self.env[res_model].search([('channel_id', '=', self.id)]).ids
        return {
            'name': ('Mapping'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': res_model,
            'view_id': False,
            'domain': [('id', 'in', mapping_ids)],
            'target': 'current',
        }

    def open_record_view(self):
        self.ensure_one()
        res_model = self._context.get('mapping_model')
        domain = [('channel_id', '=', self.id)]
        erp_ids = self.env[res_model].search(domain).mapped(self._context.get('odoo_mapping_field'))
        erp_model = ReverseDict(MAPPINGMODEL).get(res_model)
        domain = [('id', 'in', erp_ids)]
        if erp_model == 'res.partner':
            domain.append(('parent_id', '=', False))
        return {
            'name': ('Record'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': erp_model,
            'view_id': False,
            'domain': domain,
            'target': 'current',
        }

    def _get_count(self):
        for rec in self:
            domain = [('channel_id', '=', rec.id)]
            rec.channel_products = self.env['channel.template.mappings'].search_count(domain)
            rec.channel_categories = self.env['channel.category.mappings'].search_count(domain)
            rec.channel_orders = self.env['channel.order.mappings'].search_count(domain)
            domain.append(('odoo_partner.parent_id', '=', False))
            rec.channel_customers = self.env['channel.partner.mappings'].search_count(domain)

    active = fields.Boolean(default=True)
    color_index = fields.Integer(string='Color Index')

    def set_info_urls(self):
        for instance in self:
            url_info = self.get_info_urls().get(instance.channel, {})
            instance.blog_url = url_info.get('blog', 'https://webkul.com/blog/odoo-multi-channel-sale/')
            instance.store_url = url_info.get('store', 'https://store.webkul.com/Odoo-Multi-Channel-Sale.html')

    @api.model
    def get_channel_time_zone(self):
        return [(time_zone, time_zone) for time_zone in pytz.all_timezones]

    channel = fields.Selection(selection='get_channel', required=True, inverse=set_info_urls)
    name = fields.Char('Name', required=True)
    state = fields.Selection(STATE, default='draft')
    color = fields.Char(default='#000000')
    image = fields.Image(max_width=256, max_height=256)
    blog_url = fields.Char()
    store_url = fields.Char()
    debug = fields.Selection(DEBUG, default='enable', required=True)
    wk_time_zone = fields.Selection('get_channel_time_zone', string='Time Zone', required=True, default='UTC')

    environment = fields.Selection(
        selection=ENVIRONMENT,
        string='Environment',
        default='sandbox',
        help="""Set environment to  production while using live credentials.""",
    )
    is_child_store = fields.Boolean(string='Is Child-Store')
    default_store_id = fields.Many2one(
        comodel_name='multi.channel.sale',
        string='Parent Store',
        help=DefaultStore,
    )
    sku_sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        string='Sequence For SKU',
        help="""Default sequence used as sku/default code for product(in case product not have sku/default code).""",
    )
    language_id = fields.Many2one(
        comodel_name='res.lang',
        default=lambda self: self.env['res.lang'].search([], limit=1),
        help="""The language used over e-commerce store/marketplace.""",
    )

    pricelist_id = fields.Many2one('channel.pricelist.mappings', 'Pricelist Mapping')

    pricelist_name = fields.Many2one(
        comodel_name='product.pricelist',
        string='Default Pricelist',
        default=lambda self: self.env['product.pricelist'].search([], limit=1),
        help="""Select the same currency of pricelist used  over e-commerce store/marketplace.""",
    )
    default_category_id = fields.Many2one(
        comodel_name='product.category',
        string='Category',
        default=lambda self: self.env['product.category'].search([], limit=1),
        help="""Default category used as product internal category for imported products.""",
    )
    channel_default_product_categ_id = fields.Many2one(
        comodel_name='channel.category.mappings',
        string='Channel Category'
    )
    default_tax_type = fields.Selection(
        selection=TaxType,
        string='Tax Type',
        default='exclude',
        required=1
    )
    delivery_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Delivery Product',
        default=lambda self: self.env.ref('odoo_multi_channel_sale.delivery_product').id,
        domain=[('type', '=', 'service')],
        help="""Delivery product used in sale order line.""",
    )
    discount_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Discount Product',
        default=lambda self: self.env.ref('odoo_multi_channel_sale.discount_product').id,
        domain=[('type', '=', 'service')],
        help="""Discount product used in sale order line.""",
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        default=lambda self: self.env['stock.warehouse'].search([], limit=1),
        help='Warehouse used for imported product.',
    )
    location_id = fields.Many2one(
        related='warehouse_id.lot_stock_id',
        string='Stock Location',
        help='Stock Location used for imported product.',
    )
    company_id = fields.Many2one(
        related='warehouse_id.company_id',
        string='Company Id',
    )
    crm_team_id = fields.Many2one(
        comodel_name='crm.team',
        string='Sales Team',
        default=lambda self: self.env['crm.team'].search([], limit=1),
        help='Sales Team used for imported order.',
    )
    payment_term_id = fields.Many2one(
        'account.payment.term',
        string="Ecommerce Payment Term",
        help="""Default Payment Term Used In Sale Order.""")
    sales_person_id = fields.Many2one(
        'res.users',
        string="Sales Person",
        help="""Default Sales Person Used In Sale Order.""")

    utm_campaign_id = fields.Many2one(
        'utm.campaign',
        string="UTM Campaign",
        help="""Default UTM Campaign Used In Sale Order.""")
    utm_medium_id = fields.Many2one(
        'utm.medium',
        string="UTM Medium",
        help="""Default UTM Medium Used In Sale Order.""")
    utm_source_id = fields.Many2one(
        'utm.source',
        string="UTM Source",
        help="""Default UTM Source Used In Sale Order.""")

    order_state_ids = fields.One2many(
        comodel_name='channel.order.states',
        inverse_name='channel_id',
        string='Default Odoo Order States',
        help='Imported order will process in odoo on basis of these state mappings.',
        copy=True,
    )

    feed = fields.Selection(FEED, default='all', required=True)

    auto_evaluate_feed = fields.Boolean(
        string='Auto Evaluate Feed',
        default=1,
        help='Auto Evaluate Feed Just After Import.',
    )
    auto_sync_stock = fields.Boolean(
        string='Auto Sync Stock',
        help='Enable this for real time stock sync over channel.',
    )

    sync_cancel = fields.Boolean(
        string='Cancel Status',
        help='Enable for cancel status at E-commerce',
    )
    sync_invoice = fields.Boolean(
        string='Invoice Status',
        help='Enable for update invoice status at E-commerce',
    )
    sync_shipment = fields.Boolean(
        string='Shipment Status',
        help='Enable for update shipment status at E-commerce',
    )

    import_order_date = fields.Datetime(
        string='Order Imported',
        help=HelpImportOrderDate
    )

    update_order_date = fields.Datetime(
        string='Order Updated',
        help=HelpUpdateOrderDate
    )

    import_product_date = fields.Datetime(string='Product Imported')
    update_product_price = fields.Boolean(string='Update Price')
    update_product_stock = fields.Boolean(string='Update Stock')
    update_product_image = fields.Boolean(string='Update Image')
    update_product_date = fields.Datetime(string='Product Updated')

    import_customer_date = fields.Datetime(string='Customer Imported')
    update_customer_date = fields.Datetime(string='Customer Updated')
    use_api_limit = fields.Boolean(string='Use API Limit', default=True)
    api_record_limit = fields.Integer(string='API Record Limit', default=100)
    total_record_limit = fields.Integer(string='API Record Limit', default=0)

    channel_products = fields.Integer(compute='_get_count')
    channel_categories = fields.Integer(compute='_get_count')
    channel_orders = fields.Integer(compute='_get_count')
    channel_customers = fields.Integer(compute='_get_count')

    @api.constrains('api_record_limit')
    def check_api_record_limit(self):
        if self.api_record_limit <= 0:
            raise Warning("""The api record limit should be postive.""")

    @api.model
    def set_channel_date(self, operation='import', record='product'):
        current_date = fields.Datetime.now()
        if operation == 'import':
            if record == 'order':
                self.import_order_date = current_date
            elif record == 'product':
                self.import_product_date = current_date
            elif record == 'customer':
                self.import_customer_date = current_date
        else:
            if record == 'order':
                self.update_order_date = current_date
            elif record == 'product':
                self.update_product_date = current_date
            elif record == 'customer':
                self.update_customer_date = current_date
        return True

    def toggle_enviroment_value(self):
        production = self.filtered(
            lambda channel: channel.environment == 'production')
        production.write({'environment': 'sandbox'})
        (self - production).write({'environment': 'production'})
        return True

    def toggle_debug_value(self):
        enable = self.filtered(lambda channel: channel.debug == 'enable')
        enable.write({'debug': 'disable'})
        (self - enable).write({'debug': 'enable'})
        return True

    def toggle_active_value(self):
        for record in self:
            record.write({'active': not record.active})
        return True

    @api.model
    def om_format_date(self, date_string):
        timezone = self.wk_time_zone
        om_date_time = None
        message = ''
        try:
            if date_string:
                om_date_time = pytz.timezone(timezone).localize(parser.parse(date_string, ignoretz=True)).astimezone(pytz.utc).replace(tzinfo=None)
        except Exception as e:
            message += '%r' % e
        return dict(
            message=message,
            om_date_time=om_date_time
        )

    @api.model
    def create_model_objects(self, model_name, vals, **kwargs):
        """
            model_name:'res.partner'
            vals:[{'name':'demo','type':'customer'},{'name':'portal':'type':'contact'}]
        """
        message = ''
        data = None
        try:
            ObjModel = self.env[model_name]
            data = self.env[model_name]
            for val in vals:
                if kwargs.get('extra_val'):
                    val.update(kwargs.get('extra_val'))
                match = False
                if val.get('store_id'):
                    obj = ObjModel.search([('store_id', '=', val.get('store_id'))], limit=1)
                    if obj:
                        obj.write(val)
                        data += obj
                        match = True
                if not match:
                    data += ObjModel.create(val)
        except Exception as e:
            _logger.error("#1CreateModelObject Error  \n %r" % (e))
            message += "%r" % (e)
        return dict(
            data=data,
            message=message,
        )

    @api.model
    def create_product(self, name, _type='service', vals=None):
        vals = vals or {}
        vals['name'] = name
        vals['type'] = _type
        return self.env['product.product'].create(vals)

    @api.model
    def create_tax(self, name, amount, amount_type='percent', price_include=False):
        raise NotImplementedError

    @api.model
    def _create_sync(self, vals):
        if self.debug == 'enable':
            nvals = vals.copy()
            channel_vals = self.get_channel_vals()
            nvals.update(channel_vals)
            return self.env['channel.synchronization'].create(nvals)
        return self.env['channel.synchronization']

    @api.model
    def default_multi_channel_values(self):
        return self.env['res.config.settings'].sudo().get_values()

    def open_website_url(self, url, name='Open Website URL'):
        self.ensure_one()
        return {
            'name': name,
            'url': url,
            'type': 'ir.actions.act_url',
            'target': 'new',
        }

    @staticmethod
    def read_website_image_url(image_url):
        data = None
        try:
            res = requests.get(image_url)
            if res.status_code == 200:
                data = binascii.b2a_base64((res.content))
        except Exception as e:
            _logger.error("#1ReadImageUrlError  \n %r" % (e))
        return data

    @api.model
    def set_order_by_status(self, channel_id, store_id,
                            status, order_state_ids, default_order_state,
                            payment_method=None):
        result = dict(
            order_match=None,
            message=''
        )
        order_match = channel_id.match_order_mappings(store_id)
        order_state_ids = order_state_ids.filtered(
            lambda state: state.channel_state == status)
        state = order_state_ids[0] if order_state_ids else default_order_state
        if order_match and order_match.order_name.state == 'draft' and (
                state.odoo_create_invoice or state.odoo_ship_order):
            result['message'] += self.env['multi.channel.skeleton']._SetOdooOrderState(
                order_match.order_name, channel_id, status, payment_method
            )
            result['order_match'] = order_match
        return result

    def unlink_feeds_mapping(self, channel_mapping_objs, model_obj):
        model = model_obj._name
        model_dict = METAMAP.get(model)
        mapping_model = model_dict.get('mapping')
        feed_model = model_dict.get('feed')
        for channel_mapping_obj in channel_mapping_objs:
            channel_store_id = eval('channel_mapping_obj.{}'.format(model_dict.get('channel_field')))
            feed_objs = self.env[feed_model].search([
                ('store_id', '=', channel_store_id)
            ])
            for feed_obj in feed_objs:
                feed_obj.unlink()

    def _core_pre_post_write(self, obj, opr, core_model, mapping_objs, vals):
        _channel_ids = self.env['multi.channel.sale']

        for mapping_obj in mapping_objs:
            channel_id = mapping_obj.channel_id
            _channel_ids |= channel_id
            if hasattr(channel_id, '%s_mapped_%s_%s_write' % (channel_id.channel, opr, core_model)):
                vals.update(getattr(
                    channel_id, '%s_mapped_%s_%s_write' % (channel_id.channel, opr, core_model)
                )(obj, mapping_obj, vals) or vals)

        channel_ids = self.search([
            ('state', '=', 'validate'),
            ('id', 'not in', _channel_ids.ids)
        ])
        for channel_id in channel_ids:
            if hasattr(channel_id, '%s_%s_%s_write' % (channel_id.channel, opr, core_model)):
                vals.update(getattr(
                    channel_id, '%s_%s_%s_write' % (channel_id.channel, opr, core_model)
                )(obj, vals) or vals)
        return vals

    def connect_ecommerce(self):

        return True, 'Successfully connected to Ecommerce'
    





    ################ CartRover ##################

    # def action_sync_orders(self, api_key="123", api_secret="123"):

    #     payload = {
    #         "status": "any",
    #         "apiKey": api_key,
    #         "apiSecret": api_secret
    #     }

    #     if not api_key or not api_secret:
    #         print(
    #             "\nEmpty config"
    #         )
    #         return False

    #     orders = self.get_cartrover_orders(payload=payload)

    #     def is_missing_data(order):
    #         if order["items"] is None \
    #                 or order["shippingInfo"] is None \
    #                 or not order["shippingInfo"]['countryCode']:
    #             return True
    #         return False

    #     orders = list(
    #         filter(lambda order: not is_missing_data(order), orders['data'])
    #     )

    #     print(
    #         "\n++++++++++++++++++++ Success: A total number of {} valid orders found. ++++++++++++++++++++".format(
    #             len(orders)
    #         )
    #     )

    #     print("++++++++++++++++++++ Start: processing the order in Odoo ++++++++++++++++++++")
    #     if len(orders) > 0:
    #         for order in orders:

    #             order_id = str(order["orderId"])
                
    #             print("\nOrder Type {}, Order Id {}".format(order["orderType"], order["orderId"]))
    #             if order["purchaseDate"]:
    #                 purchased_date = dateutil.parser.parse(
    #                     order["purchaseDate"]
    #                 ).replace(tzinfo=None)
    #             else:
    #                 purchased_date = ''

    #             if order["estimatedShipDate"]:
    #                 estimate_ship_date = dateutil.parser.parse(
    #                     order["estimatedShipDate"]
    #                 ).replace(tzinfo=None)
    #             else:
    #                 estimate_ship_date = dateutil.parser.parse(
    #                     date.today().strftime('%Y-%m-%d')
    #                 ).replace(tzinfo=None)

    #             order_carrier_code = str(
    #                 order["shippingInfo"]["carrierCode"]
    #             )
    #             order_ship_speed = str(
    #                 order["shippingInfo"]["shippingSpeed"]
    #             )
    #             order_warehouse_id = ''
    #             order_warehouse_name = ''
    #             order_warehouse_postcode = ''

    #             account_fiscal_position, partner, company_partner, partner_for_delivery = self.get_partner(
    #                 order
    #             )

    #             team = order['additionalInfo']['salesDivision'] \
    #                 if order['additionalInfo']['salesDivision'] \
    #                 else order['orderType']
    #             sale_team = self._get_sale_team(sale_team=team)

    #             pricelist = self._get_pricelist(team)

    #             order_tag = []

    #             (
    #                 order_lines,
    #                 accept_order_payload_items,
    #             ) = self._generate_order_lines(order)

    #             sale_order_data = {
    #                 "partner_id": partner.id,
    #                 "partner_invoice_id": company_partner.id,
    #                 "partner_shipping_id": partner_for_delivery.id,
    #                 "fiscal_position_id": account_fiscal_position.id,
    #                 "origin": order_id,
    #                 "state": "sale",  ## "draft" for quotation, "sale" for confirmed sale order
    #                 "date_order": purchased_date,
    #                 "name": order_id,
    #                 'client_order_ref': order_id,
    #                 "invoice_status": "no",
    #                 "user_id": None,
    #                 "team_id": sale_team.id,
    #                 "order_line": [
    #                     (0, 0, order_line)
    #                     for order_line in order_lines
    #                 ],
    #                 "note": order['orderType'] + ' Order',
    #                 "commitment_date": estimate_ship_date,
    #                 "expected_date": estimate_ship_date,
    #                 "tag_ids": [],
    #             }

    #             if pricelist:
    #                 sale_order_data['pricelist_id'] = pricelist.id

    #             print(
    #                 "++++++++++++++++++++ Start: processing Open order {} ... ++++++++++++++++++++".format(
    #                     order_id
    #                 )
    #             )

    #             sale_order = self.env["sale.order"].search(
    #                 [("name", "=", order_id)], limit=1
    #             )

    #             if not sale_order:
    #                 # create sale order in Odoo
    #                 print(
    #                     "\n++++++++++++++++++++ Update: creating new order on odoo ++++++++++++++++++++"
    #                 )
    #                 sale_order = self.env["sale.order"].create(
    #                     sale_order_data
    #                 )

    #                 # update carrier for stock picking
    #                 self._update_stock_picking_carrier(
    #                     carrier_code=order_carrier_code, sale_order_id=sale_order.id
    #                 )

    #                 print(
    #                     "\n++++++++++++++++++++ Success: created new order on odoo ++++++++++++++++++++"
    #                 )
    #             else:
    #                 print(
    #                     "\n++++++++++++++++++++ Warning: order already exists in odoo ++++++++++++++++++++"
    #                 )

    #     return

    # @api.model
    # def _get_sale_team(self, sale_team):

    #     # search for the same team from database, and create new team if not exist. Default team
    #     search_sale_team = self.env["crm.team"].search(
    #         [("name", "=", sale_team)], limit=1
    #     )
    #     if not search_sale_team:
    #         search_sale_team = self.env["crm.team"].create(
    #             {
    #                 "name": sale_team,
    #             }
    #         )

    #     print(
    #         "\n++++++++++++++++++++ Success: getting sale team ++++++++++++++++++++"
    #     )
    #     return search_sale_team

    # @api.model
    # def _get_pricelist(self, name):
    #     # search for priclist
    #     pricelist = self.env["product.pricelist"].search(
    #         [("name", "=", name)], limit=1
    #     )

    #     print(
    #         "\n++++++++++++++++++++ Success: getting pricelist ++++++++++++++++++++"
    #     )

    #     return pricelist
    # @api.model
    # def _update_stock_picking_carrier(self, carrier_code, sale_order_id):

    #     ## search for shipping method, if not exist, pass None
    #     delivery_carrier = None
    #     list_carrier_code_ltl = ["LTL", "MTVL", "DLWS", "CURB"]
    #     if carrier_code == "FDEG":
    #         delivery_carrier = self.env["delivery.carrier"].search(
    #             [("name", "=", "Fedex")]
    #         )
    #     elif carrier_code == "UPSN":
    #         delivery_carrier = self.env["delivery.carrier"].search(
    #             [("name", "=", "UPS")]
    #         )
    #     elif carrier_code in list_carrier_code_ltl:
    #         delivery_carrier = self.env["delivery.carrier"].search(
    #             [("name", "=", "LTL")]
    #         )
    #     else:
    #         delivery_carrier = None

    #     # assign the carrier to the stock picking if exist
    #     if delivery_carrier:
    #         stock_pickings = self.env["stock.picking"].search(
    #             [("sale_id", "=", sale_order_id)]
    #         )

    #         for stock_picking in stock_pickings:
    #             stock_picking.carrier_id = delivery_carrier

    #         print(
    #             "++++++++++++++++++++ Success: update stock picking carrier - {} ++++++++++++++++++++".format(
    #                 delivery_carrier.name
    #             )
    #         )

    # @api.model
    # def _generate_order_lines(self, order_data):
    #     order_items_data = order_data["items"]

    #     def convert_to_float(str_value):
    #         try:
    #             float_value = float(str_value)
    #         except:
    #             float_value = 0
    #         return float_value

    #     order_lines = []
    #     accept_order_payload_items = []

    #     for order_item_data in order_items_data:
    #         print(order_item_data)
    #         seller_sku = order_item_data["sku"]
    #         quantity_ordered = convert_to_float(order_item_data["quantityOrdered"])
    #         item_price = convert_to_float(
    #             order_item_data["unitPrice"]
    #         )
    #         title = order_item_data["productName"]  # hardcode the title before fix
    #         item_unit_price = item_price

    #         product = self._get_product(
    #             seller_sku=seller_sku,
    #             order_type=order_data['orderType']
    #         )

    #         order_line_item = {
    #             "product_id": product.id,
    #             "name": title,
    #             "product_uom_qty": quantity_ordered,
    #             "price_unit": item_unit_price,
    #             "tax_id": False,
    #             "price_subtotal": item_price * item_unit_price,
    #         }
    #         order_lines.append(order_line_item)
    #         accept_order_payload_items.append(
    #             {
    #                 "partNumber": seller_sku,
    #                 "quantity": int(quantity_ordered),
    #                 "unitPrice": item_price,
    #                 "estimatedShipDate": "",
    #             }
    #         )
    #         print(
    #             "++++++++++++++++++++ Success: generating {} sale order lines ++++++++++++++++++++".format(
    #                 order_data['orderType'])
    #         )
    #     return order_lines, accept_order_payload_items

    # @api.model
    # def _get_order_tag(self, store_name):

    #     # add the store name to the tag
    #     tag_store_name = self.env["crm.tag"].search(
    #         [("name", "=", store_name)], limit=1
    #     )
    #     if not tag_store_name:
    #         tag_store_name = self.env["crm.tag"].create(
    #             {"name": store_name}
    #         )
    #     print(
    #         "++++++++++++++++++++ Success: getting  order tag ++++++++++++++++++++"
    #     )
    #     return tag_store_name

    # @api.model
    # def _get_product(self, seller_sku, order_type: str):

    #     ## check whether there is matching SKU in Odoo
    #     product_temp_id = self.env["product.template"].search(
    #         [
    #             ("default_code", "=", seller_sku),
    #             ("type", "in", ["product", "consu"]),
    #             ("active", "=", True),
    #         ],
    #         limit=1,
    #     )

    #     if product_temp_id:
    #         product_id = self.env["product.product"].search(
    #             [("product_tmpl_id", "=", product_temp_id.id)], limit=1
    #         )

    #     ## Otherwise check the SKU id from the Connector SKUs
    #     else:
    #         ## If no SKU was found, search or create new product in Odoo to contain all unlinked product
    #         if seller_sku == order_type.upper() + "-SHIPPING":
    #             default_code = order_type.upper() + "-SHIPPING"
    #             product_type = ["service"]
    #         elif seller_sku == order_type.upper() + "-PROMO":
    #             default_code = order_type.upper() + "-PROMO"
    #             product_type = ["service"]
    #         else:
    #             default_code = order_type.upper() + "-PRODUCT"
    #             product_type = ["product", "consu"]

    #         product_temp_id = self.env["product.template"].search(
    #             [
    #                 ("default_code", "=", default_code),
    #                 ("type", "in", product_type),
    #                 ("active", "=", True),
    #             ],
    #             limit=1,
    #         )

    #         if not product_temp_id:
    #             product_temp_id = self.env["product.template"].create(
    #                 {
    #                     "name": order_type + " Sale",
    #                     "sale_line_warn": "no-message",
    #                     "type": product_type[0],
    #                     "default_code": default_code,
    #                 }
    #             )
    #             print(
    #                 "++++++++++++++++++++ Success: Created a virtual {} product ++++++++++++++++++++".format(order_type)
    #             )

    #         product_id = self.env["product.product"].search(
    #             [("product_tmpl_id", "=", product_temp_id.id)]
    #         )

    #     print(
    #         "++++++++++++++++++++ Success: getting {} product ++++++++++++++++++++".format(order_type)
    #     )
    #     return product_id

    # def get_cartrover_orders(self, payload):

    #     url = API_DOMAIN_URL + "/listOrdersByStatus"
    #     response = requests.get(url, auth=(AUTH_USER_NAME, AUTH_PASSWORD), params=payload)
    #     response_data = json.loads(response.text)
    #     print(
    #         "\n++++++++++++++++++++ Cartrover API: get sale order reponses successfully ++++++++++++++++++++"
    #     )
    #     print(response_data)
    #     return response_data

    # def get_partner(self, order):

    #     order_shipping_info = order['shippingInfo']
        
    #     merchant = order["additionalInfo"]["salesDivision"]
    #     buyer_email = order_shipping_info["buyerEmail"]
    #     buyer_name = order_shipping_info["buyerName"]
    #     shipping_address_line1 = order_shipping_info["addressLine1"]
    #     shipping_address_line2 = order_shipping_info["addressLine2"]
    #     shipping_address_city = order_shipping_info["city"]
    #     shipping_address_state = order_shipping_info["stateOrRegion"]
    #     shipping_address_post_code = order_shipping_info["postalCode"]
    #     shipping_address_country_code = order_shipping_info["countryCode"]
    #     shipping_address_phone = order_shipping_info["phone"]

    #     # get country
    #     country = self.env["res.country"].search(
    #         [("code", "=", shipping_address_country_code)], limit=1
    #     )

    #     # get state, if not exist, create a new one
    #     state = self.env["res.country.state"].search(
    #         [
    #             ("country_id", "=", country.id),
    #             "|",
    #             ("code", "=", shipping_address_state),
    #             ("name", "=", shipping_address_state),
    #         ],
    #         limit=1,
    #     )
    #     if not state:
    #         state = self.env["res.country.state"].create(
    #             {
    #                 "country_id": country.id,
    #                 "name": shipping_address_state,
    #                 "code": shipping_address_state,
    #             }
    #         )

    #     # create account_fiscal_position if there isn't
    #     account_fiscal_position = self.env["account.fiscal.position"].search(
    #         [
    #             ("name", "=", shipping_address_state)
    #         ],
    #         limit=1,
    #     )

    #     if not account_fiscal_position:
    #         account_fiscal_position = self.env["account.fiscal.position"].create(
    #             {
    #                 "id": state.id,
    #                 "country_id": country.id,
    #                 "name": shipping_address_state,
    #             }
    #         )

    #     partner_add_info = {
    #         "street": shipping_address_line1,
    #         "street2": shipping_address_line2,
    #         "city": shipping_address_city,
    #         "state_id": state.id,
    #         "country_id": country.id,
    #         "zip": shipping_address_post_code,
    #         "phone": shipping_address_phone,
    #         "customer_rank": 1,
    #     }

    #     # create company partner if not exist
    #     company_partner = self.env["res.partner"].search(
    #         [
    #             ("name", "=", merchant),
    #             ("buyer_name", "=", merchant),
    #             ("email", "=", buyer_email),
    #         ]
    #     )

    #     if not company_partner:
    #         company_partner = self.env["res.partner"].create(
    #             {
    #                 "email": buyer_email,
    #                 "name": merchant,
    #                 "buyer_email": buyer_email,
    #                 "buyer_name": merchant,
    #                 "type": "contact",
    #                 **partner_add_info,
    #             }
    #         )

    #     # create customer partner if not exist
    #     partner = self.env["res.partner"].search(
    #         [
    #             ("buyer_name", "=", buyer_name),
    #             ("name", "=", buyer_name),
    #             ("email", "=", buyer_email),
    #         ],
    #         limit=1,
    #     )

    #     if not partner:
    #         partner = self.env["res.partner"].create(
    #             {
    #                 "email": buyer_email,
    #                 "name": buyer_name,
    #                 "buyer_email": buyer_email,
    #                 "buyer_name": buyer_name,
    #                 "type": "contact",
    #                 **partner_add_info,
    #             }
    #         )

    #     ## get the partner for delivery purpose
    #     if (
    #             (partner.name == buyer_name)
    #             and (partner.street == shipping_address_line1)
    #             and (partner.street2 == shipping_address_line2)
    #             and (partner.zip == shipping_address_post_code)
    #     ):
    #         partner_for_delivery = partner
    #     else:
    #         # search for delivery partner, if not exist, create a new delivery partner if the shipping address is different from primary address
    #         partner_for_delivery = self.env["res.partner"].search(
    #             [
    #                 ("parent_id", "=", partner.id),
    #                 ("name", "=", buyer_name),
    #                 ("type", "=", "delivery"),
    #                 ("street", "=", shipping_address_line1),
    #                 ("street2", "=", shipping_address_line2),
    #                 ("city", "=", shipping_address_city),
    #                 ("zip", "=", shipping_address_post_code),
    #             ],
    #             limit=1,
    #         )

    #         if not partner_for_delivery:
    #             partner_for_delivery = self.env["res.partner"].create(
    #                 {
    #                     "parent_id": partner.id,
    #                     "name": buyer_name,
    #                     "type": "delivery",
    #                     **partner_add_info,
    #                 }
    #             )

    #     print(
    #         "\n++++++++++++++++++++ Success: getting partner ++++++++++++++++++++"
    #     )
    #     return account_fiscal_position, partner, company_partner, partner_for_delivery
