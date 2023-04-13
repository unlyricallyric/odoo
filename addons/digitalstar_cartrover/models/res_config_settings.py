# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.tools.safe_eval import dateutil
from datetime import date
import requests
import json

AUTH_USER_NAME = "DigitalStarAPI"
AUTH_PASSWORD = "r@4?J]p8PgB6XZLv"
API_DOMAIN_URL = "http://dsecomapinetcore-test.us-east-1.elasticbeanstalk.com/api"

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    api_key = fields.Char(string="API Key", required=True, config_parameter='digitalstar_cartrover.api_key')
    api_secret = fields.Char(string="API Secret", required=True, config_parameter='digitalstar_cartrover.api_secret')


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

                partner, partner_for_delivery = self.get_partner(
                    order
                )

                team = order['additionalInfo']['salesDivision'] \
                    if order['additionalInfo']['salesDivision'] \
                    else order['orderType']
                sale_team = self._get_sale_team(sale_team=team)

                pricelist = self._get_pricelist(team)

                order_tag = []

                (
                    order_lines,
                    accept_order_payload_items,
                ) = self._generate_order_lines(order)

                sale_order_data = {
                    "partner_id": partner.id,
                    "partner_shipping_id": partner_for_delivery.id,
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
    def _get_pricelist(self, name):
        # search for priclist
        pricelist = self.env["product.pricelist"].search(
            [("name", "=", name)], limit=1
        )

        print(
            "\n++++++++++++++++++++ Success: getting pricelist ++++++++++++++++++++"
        )

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

        url = API_DOMAIN_URL + "/testOrders"
        response = requests.get(url, auth=(AUTH_USER_NAME, AUTH_PASSWORD), params=payload)
        response_data = json.loads(response.text)
        print(
            "\n++++++++++++++++++++ Cartrover API: get sale order reponses successfully ++++++++++++++++++++"
        )
        print(response_data)
        return response_data

    def get_partner(self, order):

        order_shipping_info = order['shippingInfo']

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

        # search for the partner id from database, if not exist, create new partner
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
        return partner, partner_for_delivery
