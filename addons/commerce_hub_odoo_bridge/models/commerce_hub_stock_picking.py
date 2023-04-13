import requests
from odoo import api, models, fields, _

API_KEY = "51174ZcuEXaQ"
API_SECRET = "r2DPCFu0jTuoTfn"
AUTH_USER_NAME = "DigitalStarAPI"
AUTH_PASSWORD = "r@4?J]p8PgB6XZLv"
API_DOMAIN_URL = "http://dsecomapinetcore-test.us-east-1.elasticbeanstalk.com/api"

class CommerceHub(models.Model):
    _inherit = 'stock.picking'

    def upload_tracking_info(self):
        print("##################  COMMERCEHUB ####################")
        carrier = self.env['delivery.carrier'].search(
            [
                ('id', '=', self.carrier_id.id)
            ],
            limit=1
        )

        if carrier:
            carrier_name = carrier.name
            tracking_no = self.carrier_tracking_ref
            order_id = self.origin

            location = self.location_id
            warehouse = location.warehouse_id

            self.update_order_status(order_id, carrier_name, tracking_no, warehouse.name)
            print("Carrier Name: ")
            print(carrier_name)
            print("Tracking number: ")
            print(tracking_no)
            print("Order ID: ")
            print(order_id)
            print("Location ID: ")
            print(warehouse.name)

    def update_order_status(self, order_id, carrier_name, tracking_no, warehouse_name):
        url = API_DOMAIN_URL + "/updateOrderStatus"
        params = {
            "orderID": order_id,
            "apiKey": API_KEY,
            "apiSecret": API_SECRET
        }

        data = {
            "order_status": "shipped",
            "shipments": [
                {
                    "carrier": carrier_name,
                    "tracking_no": tracking_no,
                    "whs_location": warehouse_name
                }
            ]
        }

        response = requests.post(url, auth=(AUTH_USER_NAME, AUTH_PASSWORD), params=params, json=data)

        print(response.content)

            
        