# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
import requests
import json
from odoo.tools.safe_eval import dateutil
from dateutil import parser
from datetime import date
from logging import getLogger

from odoo import fields, models, api, _
_logger = getLogger(__name__)

AUTH_USER_NAME = "DigitalStarAPI"
AUTH_PASSWORD = "r@4?J]p8PgB6XZLv"
API_DOMAIN_URL = "http://dsecomapinetcore-test.us-east-1.elasticbeanstalk.com/api"

METAMAP = {
    'product.category': {
        'model': 'channel.category.mappings',
        'local_field': 'odoo_category_id',
        'remote_field': 'store_category_id'
    },
    'product.template': {
        'model': 'channel.template.mappings',
        'local_field': 'odoo_template_id',
        'remote_field': 'store_product_id'
    },
    'product.product': {
        'model': 'channel.product.mappings',
        'local_field': 'erp_product_id',
        'remote_field': 'store_variant_id'
    }
}
IMPORT_OPR = [
    ('product.template', 'Product'),
    ('sale.order', 'Order'),
    ('product.category', 'Category'),
    ('res.partner', 'Customer'),
    ('delivery.carrier', 'Shipping Method'),
]

class Transaction:
    def __init__(self, channel, *args, **kwargs):
        self.instance = channel
        self.channel = channel.channel
        self.env = channel.env
        self._cr = channel._cr
        self.evaluate_feed = channel.auto_evaluate_feed
        self.display_message = channel.display_message

    def import_data(self, object, **kw):
        msg = "Current channel doesn't allow it."

        success_ids = []
        error_ids = []
        create_ids = []
        update_ids = []
        kw.update(
            page_size=self.instance.api_record_limit
        )
        page, total_record_limit = 0, self.instance.total_record_limit
        if hasattr(self.instance, 'import_{}'.format(self.channel)):
            msg = ''
            try:
                while True:
                    page += 1
                    _logger.debug(">> page >> : %r", page)
                    s_ids, e_ids, feeds = [], [], False
                    data_list, kw = getattr(
                        self.instance, 'import_{}'.format(self.channel))(object, **kw), kw
                    kw = data_list[1] if isinstance(data_list, tuple) else kw
                    data_list = [] if data_list in [None, False, ''] or len(data_list) < 1 else data_list[0]
                    if data_list and type(data_list) is list:
                        kw['last_id'] = data_list[-1].get('store_id')

                    if data_list:
                        objectmapping = self.getFeedObjectDictionary()
                        if object in objectmapping:
                            # rohit with_company(id)
                            s_ids, e_ids, feeds = self.env[objectmapping.get(object)].with_context(
                                channel_id=self.instance
                            ).with_company(self.instance.company_id.id)._create_feeds(data_list)
                        elif object == 'product.attribute':
                            data_list = data_list.get('create_ids', []) if data_list.get('create_ids') else data_list.get('update_ids', [])
                            msg = "<div class='alert alert-success' role='alert'><h3 class='alert-heading'><i class='fa fa-smile-o'/>  Congratulations !</h3><hr><span class='badge badge-pill badge-success'>Success</span>All attributes are synced along with the <span class='font-weight-bold'> {} attribute sets</span></div>".format(len(data_list)) if data_list else "<div class='alert alert-danger' role='alert'>Attributes are failed to import.</div>"
                        else:
                            raise Exception('Invalid object type')
                    else:
                        msg = "No Data Available to Import!"
                        raise Exception(kw.get('message'))

                    # NOTE: To handle api_limit==1 infinity loop
                    if kw.get('page_size', 0) == 1:
                        if locals().get('old_last_id') == kw.get('last_id'):
                            break
                        else:
                            old_last_id = kw.get('last_id')

                    self._cr.commit()
                    success_ids.extend(s_ids)
                    error_ids.extend(e_ids)
                    if self.evaluate_feed and feeds:
                        mapping_ids = feeds.with_context(get_mapping_ids=True).import_items()
                        create_ids.extend([mapping.id for mapping in mapping_ids.get('create_ids')])
                        update_ids.extend([mapping.id for mapping in mapping_ids.get('update_ids')])
                        self._cr.commit()
                    if len(data_list) < kw.get('page_size'):
                        break
                    if total_record_limit and page * self.instance.api_record_limit >= total_record_limit:
                        break
            except Exception as e:
                if not msg:
                    msg = f'Something went wrong: `{e.args[0]}`'
                _logger.exception(msg)
                msg = f"<div class='alert alert-danger' role='alert'><h3 class='alert-heading'><i class='fa fa-frown-o'/>  Exception !</h3><hr><span class='badge badge-pill badge-danger'> {msg} </span></div>"

            if not msg:
                operation = dict(IMPORT_OPR)[object]
                debug = self.instance.debug
                last_id = kw.get('last_id')
                ext_msg = kw.get('ext_msg')
                msg = self.getActionMessage(msg, success_ids, error_ids, create_ids, update_ids, last_id, debug, operation, ext_msg)
            if not msg:
                msg += f"<div class='alert alert-danger' role='alert'><h3 class='alert-heading'><i class='fa fa-frown-o'/>  Sorry !</h3><hr><span class='badge badge-pill badge-danger'> 404 </span> <span class='font-weight-bold'> No records found for applied filter.</span></div>"
        return self.display_message(msg)

    def getFeedObjectDictionary(self):
        return {'product.category': 'category.feed', 'product.template': 'product.feed', 'res.partner': 'partner.feed', 'sale.order': 'order.feed', 'delivery.carrier': 'shipping.feed'}

    def export_data(self, object, object_ids, operation='export'):
        msg = "Selected Channel doesn't allow it."
        success_ids, error_ids = [], []

        mappings = self.env[METAMAP.get(object).get('model')].search(
            [
                ('channel_id', '=', self.instance.id),
                (
                    METAMAP.get(object).get('local_field'),
                    'in',
                    object_ids
                ),
            ]
        )

        if operation == 'export' and hasattr(self.instance, 'export_{}'.format(self.channel)):
            msg = ''
            local_ids = mappings.mapped(
                lambda mapping: int(getattr(mapping, METAMAP.get(object).get('local_field')))
            )
            local_ids = set(object_ids) - set(local_ids)
            if not local_ids:
                return self.display_message(
                    """<p style='color:orange'>
                        Selected records have already been exported.
                    </p>"""
                )
            operation = 'exported'
            for record in self.env[object].browse(local_ids):
                res, remote_object = getattr(self.instance, 'export_{}'.format(self.channel))(record)
                if res:
                    self.create_mapping(record, remote_object)
                    success_ids.append(record.id)
                else:
                    error_ids.append(record.id)

        elif operation == 'update' and hasattr(self.instance, 'update_{}'.format(self.channel)):
            msg = ''
            local_ids = mappings.filtered_domain([
                ('need_sync', '=', 'yes')]).mapped(
                lambda mapping: int(getattr(mapping, METAMAP.get(object).get('local_field')))
            )
            if not local_ids:
                if mappings:
                    return self.display_message(
                        """<p style='color:orange'>
                            Nothing to update on selected records.
                        </p>"""
                    )
                else:
                    return self.display_message(
                        """<p style='color:orange'>
                            Selected records haven't been exported yet.
                        </p>"""
                    )
            operation = 'updated'
            for record in self.env[object].browse(local_ids):
                res, remote_object = getattr(self.instance, 'update_{}'.format(self.channel))(
                    record=record,
                    get_remote_id=self.get_remote_id
                )
                if res:
                    success_ids.append(record.id)
                else:
                    error_ids.append(record.id)

        self.env[METAMAP.get(object).get('model')].search([
            ('channel_id', '=', self.instance.id),
            (
                METAMAP.get(object).get('local_field'),
                'in',
                success_ids
            )]).write({'need_sync': 'no'})

        if not msg:
            if success_ids:
                msg += f"<p style='color:green'>{success_ids} {operation}.</p>"
            if error_ids:
                msg += f"<p style='color:red'>{error_ids} not {operation}.</p>"
        return self.display_message(msg)

    def get_remote_id(self, record):
        mapping = self.env[METAMAP.get(record._name).get('model')].search(
            [
                ('channel_id', '=', self.instance.id),
                (METAMAP.get(record._name).get('local_field'), '=', record.id)
            ]
        )
        return getattr(mapping, METAMAP.get(record._name).get('remote_field'))

    def create_mapping(self, local_record, remote_object):
        if local_record._name == 'product.category':
            self.env['channel.category.mappings'].create(
                {
                    'channel_id': self.instance.id,
                    'ecom_store': self.instance.channel,
                    'category_name': local_record.id,
                    'odoo_category_id': local_record.id,
                    'store_category_id': remote_object.get('id') if isinstance(remote_object, dict) else remote_object.id,
                    'operation': 'export',
                }
            )
        elif local_record._name == 'product.template':
            self.env['channel.template.mappings'].create(
                {
                    'channel_id': self.instance.id,
                    'ecom_store': self.instance.channel,
                    'template_name': local_record.id,
                    'odoo_template_id': local_record.id,
                    'default_code': local_record.default_code,
                    'barcode': local_record.barcode,
                    'store_product_id': remote_object.get('id') if isinstance(remote_object, dict) else remote_object.id,
                    'operation': 'export',
                }
            )
            remote_variants = remote_object.get('variants') if isinstance(remote_object, dict) else remote_object.variants
            for local_variant, remote_variant in zip(local_record.product_variant_ids, remote_variants):
                self.env['channel.product.mappings'].create(
                    {
                        'channel_id': self.instance.id,
                        'ecom_store': self.instance.channel,
                        'product_name': local_variant.id,
                        'erp_product_id': local_variant.id,
                        'default_code': local_variant.default_code,
                        'barcode': local_variant.barcode,
                        'store_product_id': remote_object.get('id') if isinstance(remote_object, dict) else remote_object.id,
                        'store_variant_id': remote_variant.get('id') if isinstance(remote_variant, dict) else remote_variant.id,
                    }
                )

    def getActionMessage(self, msg, success_ids, error_ids, create_ids, update_ids, last_id, debug, operation, ext_msg):
        if success_ids:
            msg += (f"<div class='alert alert-success' role='alert'>"
                    f"<h3 class='alert-heading'><i class='fa fa-smile-o'/>  Congratulations !</h3>"
                    f"<hr><span class='badge badge-pill badge-success'>Success</span>"
                    f"Data of the {operation} has been successfully imported. "
                    f"<span class='font-weight-bold'> {len(success_ids)} records of {operation} has been created/updated at Odoo</span></div>")
            if debug == 'enable':
                msg += f"<hr><div class='alert alert-success' role='alert'><br/>Ids of the records are <br/>{success_ids}.</div>"
        if error_ids:
            msg += (f"<div class='alert alert-danger' role='alert'>"
                    f"<h3 class='alert-heading'><i class='fa fa-frown-o'/>  Sorry !</h3>"
                    f"<hr><span class='badge badge-pill badge-danger'>Success</span>"
                    f"Data of the {operation} has been failed to imported. "
                    f"<span class='font-weight-bold'> {len(error_ids)} records of {operation} has been failed to create/update at Odoo</span></div>")
            if debug == 'enable':
                msg += f"<hr><div class='alert alert-danger' role='alert'><br/>Failed records are <br/>{error_ids}.</div>"
        if create_ids:
            msg += (f"<div class='alert alert-warning' role='alert'>"
                    f"<h3 class='alert-heading'><i class='fa fa-check-circle'/>  Great !</h3>"
                    f"<hr><span class='badge badge-pill badge-warning'>Imported</span>"
                    f"Data of the {operation} has been successfully created. "
                    f"<span class='font-weight-bold'> {len(create_ids)} records of {operation} has been created at Odoo</span></div>")
            if debug == 'enable':
                msg += f"<hr><div class='alert alert-warning' role='alert'><br/>Ids of the records are <br/>{create_ids}.</div>"
        if update_ids:
            msg += (f"<div class='alert alert-warning' role='alert'>"
                    f"<h3 class='alert-heading'><i class='fa fa-check-circle'/>  Yippee !</h3>"
                    f"<hr><span class='badge badge-pill badge-warning'>Updated</span>"
                    f"Data of the {operation} has been successfully updated. "
                    f"<span class='font-weight-bold'> {len(update_ids)} records of {operation} has been updated at Odoo</span></div>")
            if debug == 'enable':
                msg += f"<hr><div class='alert alert-warning' role='alert'><br/>Ids of the records are <br/>{update_ids}.</div>"
        if ext_msg:
            msg += (f"<div class='alert alert-info' role='alert'>"
                    f"<h3 class='alert-heading'><i class='fa fa-info-circle'/>  Info !</h3>"
                    f"<hr><span class='badge badge-pill badge-info'>Information</span>"
                    f"Data of the {operation} has been failed to imported. <span class='font-weight-bold'> {ext_msg} </span></div>")
        if last_id:
            msg += f"<hr><span class='badge badge-pill badge-info'>Last Imported Record :{last_id}.</span>"
        return msg



################ CartRover ##################

    def action_sync_orders(self, api_key="123", api_secret="123"):

        payload = {
            "status": "any",
            "apiKey": api_key,
            "apiSecret": api_secret
        }

        if not api_key or not api_secret:
            print(
                "\nEmpty config"
            )
            return False

        orders = self.get_cartrover_orders(payload=payload)

        def is_missing_data(order):
            if order["items"] is None \
                    or order["shippingInfo"] is None \
                    or not order["shippingInfo"]['countryCode']:
                return True
            return False

        orders = list(
            filter(lambda order: not is_missing_data(order), orders['data'])
        )

        print(
            "\n++++++++++++++++++++ Success: A total number of {} valid orders found. ++++++++++++++++++++".format(
                len(orders)
            )
        )

        print("++++++++++++++++++++ Start: processing the order in Odoo ++++++++++++++++++++")
        if len(orders) > 0:
            for order in orders:

                order_id = str(order["orderId"])
                
                print("\nOrder Type {}, Order Id {}".format(order["orderType"], order["orderId"]))
                if order["purchaseDate"]:
                    purchased_date = dateutil.parser.parse(
                        order["purchaseDate"]
                    ).replace(tzinfo=None)
                else:
                    purchased_date = ''

                if order["estimatedShipDate"]:
                    estimate_ship_date = dateutil.parser.parse(
                        order["estimatedShipDate"]
                    ).replace(tzinfo=None)
                else:
                    estimate_ship_date = dateutil.parser.parse(
                        date.today().strftime('%Y-%m-%d')
                    ).replace(tzinfo=None)

                order_carrier_code = str(
                    order["shippingInfo"]["carrierCode"]
                )
                order_ship_speed = str(
                    order["shippingInfo"]["shippingSpeed"]
                )
                order_warehouse_id = ''
                order_warehouse_name = ''
                order_warehouse_postcode = ''

                currency_code = order["currencyCode"]

                currency_id = self.get_currency_id_by_code(currency_code)

                account_fiscal_position, partner, company_partner, partner_for_delivery = self.get_partner(
                    order
                )

                team = order['additionalInfo']['salesDivision'] \
                    if order['additionalInfo']['salesDivision'] \
                    else order['orderType']
                sale_team = self._get_sale_team(sale_team=team)

                pricelist = self._get_pricelist(team, currency_id)

                order_tag = []

                (
                    order_lines,
                    accept_order_payload_items,
                ) = self._generate_order_lines(order)

                sale_order_data = {
                    "partner_id": partner.id,
                    "partner_invoice_id": company_partner.id,
                    "partner_shipping_id": partner_for_delivery.id,
                    "fiscal_position_id": account_fiscal_position.id,
                    "origin": order_id,
                    "state": "sale",  ## "draft" for quotation, "sale" for confirmed sale order
                    "date_order": purchased_date,
                    "name": order_id,
                    'client_order_ref': order_id,
                    "invoice_status": "no",
                    "user_id": None,
                    "team_id": sale_team.id,
                    "order_line": [
                        (0, 0, order_line)
                        for order_line in order_lines
                    ],
                    "note": order['orderType'] + ' Order',
                    "commitment_date": estimate_ship_date,
                    "expected_date": estimate_ship_date,
                    "tag_ids": [],
                }

                if pricelist:
                    print('$$$$$$$$$$$$$$$$$$$ price list ID is ########################')
                    print(pricelist.id)
                    sale_order_data['pricelist_id'] = pricelist.id

                print(
                    "++++++++++++++++++++ Start: processing Open order {} ... ++++++++++++++++++++".format(
                        order_id
                    )
                )

                sale_order = self.env["sale.order"].search(
                    [("name", "=", order_id)], limit=1
                )

                if not sale_order:
                    # create sale order in Odoo
                    print(
                        "\n++++++++++++++++++++ Update: creating new order on odoo ++++++++++++++++++++"
                    )
                    sale_order = self.env["sale.order"].create(
                        sale_order_data
                    )

                    # update carrier for stock picking
                    self._update_stock_picking_carrier(
                        carrier_code=order_carrier_code, sale_order_id=sale_order.id
                    )

                    print(
                        "\n++++++++++++++++++++ Success: created new order on odoo ++++++++++++++++++++"
                    )
                else:
                    print(
                        "\n++++++++++++++++++++ Warning: order already exists in odoo ++++++++++++++++++++"
                    )

        return

    @api.model
    def _get_sale_team(self, sale_team):

        # search for the same team from database, and create new team if not exist. Default team
        search_sale_team = self.env["crm.team"].search(
            [("name", "=", sale_team)], limit=1
        )
        if not search_sale_team:
            search_sale_team = self.env["crm.team"].create(
                {
                    "name": sale_team,
                }
            )

        print(
            "\n++++++++++++++++++++ Success: getting sale team ++++++++++++++++++++"
        )
        return search_sale_team

    @api.model
    def _get_pricelist(self, name, currency_id):
        # search for priclist
        pricelist = self.env["product.pricelist"].search(
            [("name", "=", name)], limit=1
        )

        if not pricelist:
            print('Price list not found!', name)
            create_pricelist = self.env["product.pricelist"].create(
                {
                    "name": name,
                    "currency_id": currency_id
                }
            )
            print(
                "\n++++++++++++++++++++ Success: created new pricelist ++++++++++++++++++++"
            )
            pricelist = create_pricelist

        return pricelist

    @api.model
    def _update_stock_picking_carrier(self, carrier_code, sale_order_id):

        ## search for shipping method, if not exist, pass None
        delivery_carrier = None
        list_carrier_code_ltl = ["LTL", "MTVL", "DLWS", "CURB"]
        if carrier_code == "FDEG":
            delivery_carrier = self.env["delivery.carrier"].search(
                [("name", "=", "Fedex")]
            )
        elif carrier_code == "UPSN":
            delivery_carrier = self.env["delivery.carrier"].search(
                [("name", "=", "UPS")]
            )
        elif carrier_code in list_carrier_code_ltl:
            delivery_carrier = self.env["delivery.carrier"].search(
                [("name", "=", "LTL")]
            )
        else:
            delivery_carrier = None

        # assign the carrier to the stock picking if exist
        if delivery_carrier:
            stock_pickings = self.env["stock.picking"].search(
                [("sale_id", "=", sale_order_id)]
            )

            for stock_picking in stock_pickings:
                stock_picking.carrier_id = delivery_carrier

            print(
                "++++++++++++++++++++ Success: update stock picking carrier - {} ++++++++++++++++++++".format(
                    delivery_carrier.name
                )
            )

    @api.model
    def _generate_order_lines(self, order_data):
        order_items_data = order_data["items"]

        def convert_to_float(str_value):
            try:
                float_value = float(str_value)
            except:
                float_value = 0
            return float_value

        order_lines = []
        accept_order_payload_items = []

        for order_item_data in order_items_data:
            print(order_item_data)
            seller_sku = order_item_data["sku"]
            quantity_ordered = convert_to_float(order_item_data["quantityOrdered"])
            item_price = convert_to_float(
                order_item_data["unitPrice"]
            )
            title = order_item_data["productName"]  # hardcode the title before fix
            item_unit_price = item_price

            product = self._get_product(
                seller_sku=seller_sku,
                order_type=order_data['orderType']
            )

            order_line_item = {
                "product_id": product.id,
                "name": title,
                "product_uom_qty": quantity_ordered,
                "price_unit": item_unit_price,
                "tax_id": False,
                "price_subtotal": item_price * item_unit_price,
            }
            order_lines.append(order_line_item)
            accept_order_payload_items.append(
                {
                    "partNumber": seller_sku,
                    "quantity": int(quantity_ordered),
                    "unitPrice": item_price,
                    "estimatedShipDate": "",
                }
            )
            print(
                "++++++++++++++++++++ Success: generating {} sale order lines ++++++++++++++++++++".format(
                    order_data['orderType'])
            )
        return order_lines, accept_order_payload_items

    @api.model
    def _get_order_tag(self, store_name):

        # add the store name to the tag
        tag_store_name = self.env["crm.tag"].search(
            [("name", "=", store_name)], limit=1
        )
        if not tag_store_name:
            tag_store_name = self.env["crm.tag"].create(
                {"name": store_name}
            )
        print(
            "++++++++++++++++++++ Success: getting  order tag ++++++++++++++++++++"
        )
        return tag_store_name

    @api.model
    def _get_product(self, seller_sku, order_type: str):

        ## check whether there is matching SKU in Odoo
        product_temp_id = self.env["product.template"].search(
            [
                ("default_code", "=", seller_sku),
                ("type", "in", ["product", "consu"]),
                ("active", "=", True),
            ],
            limit=1,
        )

        if product_temp_id:
            product_id = self.env["product.product"].search(
                [("product_tmpl_id", "=", product_temp_id.id)], limit=1
            )

        ## Otherwise check the SKU id from the Connector SKUs
        else:
            ## If no SKU was found, search or create new product in Odoo to contain all unlinked product
            if seller_sku == order_type.upper() + "-SHIPPING":
                default_code = order_type.upper() + "-SHIPPING"
                product_type = ["service"]
            elif seller_sku == order_type.upper() + "-PROMO":
                default_code = order_type.upper() + "-PROMO"
                product_type = ["service"]
            else:
                default_code = order_type.upper() + "-PRODUCT"
                product_type = ["product", "consu"]

            product_temp_id = self.env["product.template"].search(
                [
                    ("default_code", "=", default_code),
                    ("type", "in", product_type),
                    ("active", "=", True),
                ],
                limit=1,
            )

            if not product_temp_id:
                product_temp_id = self.env["product.template"].create(
                    {
                        "name": order_type + " Sale",
                        "sale_line_warn": "no-message",
                        "type": product_type[0],
                        "default_code": default_code,
                    }
                )
                print(
                    "++++++++++++++++++++ Success: Created a virtual {} product ++++++++++++++++++++".format(order_type)
                )

            product_id = self.env["product.product"].search(
                [("product_tmpl_id", "=", product_temp_id.id)]
            )

        print(
            "++++++++++++++++++++ Success: getting {} product ++++++++++++++++++++".format(order_type)
        )
        return product_id

    def get_cartrover_orders(self, payload):

        url = API_DOMAIN_URL + "/listOrdersByStatus"
        response = requests.get(url, auth=(AUTH_USER_NAME, AUTH_PASSWORD), params=payload)
        response_data = json.loads(response.text)
        print(
            "\n++++++++++++++++++++ Cartrover API: get sale order reponses successfully ++++++++++++++++++++"
        )
        print(response_data)
        return response_data
    
    def get_currency_id_by_code(self, currency_code):
        currency = self.env['res.currency'].search(
            [
                ('name', '=', currency_code)
            ],
            limit=1
        )
        return currency.id if currency else 2
    

    def get_partner(self, order):

        order_shipping_info = order['shippingInfo']
        
        merchant = order["additionalInfo"]["salesDivision"]
        buyer_email = order_shipping_info["buyerEmail"]
        buyer_name = order_shipping_info["buyerName"]
        shipping_address_line1 = order_shipping_info["addressLine1"]
        shipping_address_line2 = order_shipping_info["addressLine2"]
        shipping_address_city = order_shipping_info["city"]
        shipping_address_state = order_shipping_info["stateOrRegion"]
        shipping_address_post_code = order_shipping_info["postalCode"]
        shipping_address_country_code = order_shipping_info["countryCode"]
        shipping_address_phone = order_shipping_info["phone"]

        # get country
        country = self.env["res.country"].search(
            [("code", "=", shipping_address_country_code)], limit=1
        )

        # get state, if not exist, create a new one
        state = self.env["res.country.state"].search(
            [
                ("country_id", "=", country.id),
                "|",
                ("code", "=", shipping_address_state),
                ("name", "=", shipping_address_state),
            ],
            limit=1,
        )
        if not state:
            state = self.env["res.country.state"].create(
                {
                    "country_id": country.id,
                    "name": shipping_address_state,
                    "code": shipping_address_state,
                }
            )

        # create account_fiscal_position if there isn't
        account_fiscal_position = self.env["account.fiscal.position"].search(
            [
                ("name", "=", shipping_address_state)
            ],
            limit=1,
        )

        if not account_fiscal_position:
            account_fiscal_position = self.env["account.fiscal.position"].create(
                {
                    "id": state.id,
                    "country_id": country.id,
                    "name": shipping_address_state,
                }
            )

        partner_add_info = {
            "street": shipping_address_line1,
            "street2": shipping_address_line2,
            "city": shipping_address_city,
            "state_id": state.id,
            "country_id": country.id,
            "zip": shipping_address_post_code,
            "phone": shipping_address_phone,
            "customer_rank": 1,
        }

        # create company partner if not exist
        company_partner = self.env["res.partner"].search(
            [
                ("name", "=", merchant),
                ("buyer_name", "=", merchant),
                ("email", "=", buyer_email),
            ]
        )

        if not company_partner:
            company_partner = self.env["res.partner"].create(
                {
                    "email": buyer_email,
                    "name": merchant,
                    "buyer_email": buyer_email,
                    "buyer_name": merchant,
                    "type": "contact",
                    **partner_add_info,
                }
            )

        # create customer partner if not exist
        partner = self.env["res.partner"].search(
            [
                ("buyer_name", "=", buyer_name),
                ("name", "=", buyer_name),
                ("email", "=", buyer_email),
            ],
            limit=1,
        )

        if not partner:
            partner = self.env["res.partner"].create(
                {
                    "email": buyer_email,
                    "name": buyer_name,
                    "buyer_email": buyer_email,
                    "buyer_name": buyer_name,
                    "type": "contact",
                    **partner_add_info,
                }
            )

        ## get the partner for delivery purpose
        if (
                (partner.name == buyer_name)
                and (partner.street == shipping_address_line1)
                and (partner.street2 == shipping_address_line2)
                and (partner.zip == shipping_address_post_code)
        ):
            partner_for_delivery = partner
        else:
            # search for delivery partner, if not exist, create a new delivery partner if the shipping address is different from primary address
            partner_for_delivery = self.env["res.partner"].search(
                [
                    ("parent_id", "=", partner.id),
                    ("name", "=", buyer_name),
                    ("type", "=", "delivery"),
                    ("street", "=", shipping_address_line1),
                    ("street2", "=", shipping_address_line2),
                    ("city", "=", shipping_address_city),
                    ("zip", "=", shipping_address_post_code),
                ],
                limit=1,
            )

            if not partner_for_delivery:
                partner_for_delivery = self.env["res.partner"].create(
                    {
                        "parent_id": partner.id,
                        "name": buyer_name,
                        "type": "delivery",
                        **partner_add_info,
                    }
                )

        print(
            "\n++++++++++++++++++++ Success: getting partner ++++++++++++++++++++"
        )
        return account_fiscal_position, partner, company_partner, partner_for_delivery