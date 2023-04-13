# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from logging import getLogger
from re import sub
from time import sleep

_logger = getLogger(__name__)

try:
	import shopify
except ImportError:
	_logger.error('**Install ShopifyApi python package cmd: `pip3 install ShopifyApi==8.0.0` or `pip3 install ShopifyApi==11.0.0`')
else:
	if shopify.VERSION not in ['8.0.0','11.0.0']:
		_logger.error('**ShopifyApi v8.0.0 or v11.0.0 required. `pip3 install ShopifyApi==8.0.0` or `pip3 install ShopifyApi==11.0.0`')

# API_VERSION = '2020-07'
API_VERSION = '2022-04'

class Bridge:
	def __init__(self,url,api_key,password,channel_id=False,pricelist_id=False,**kw):
		if '//' not in url:
			url = f'https://{url}'
		self.id           = channel_id
		self.pricelist_id = pricelist_id
		self.url          = f'{url}/admin/api/{API_VERSION}'
		self.api_key      = api_key
		self.password     = password
		self.location_id  = kw.get('location_id')

	def __enter__(self):
		if shopify.VERSION == '11.0.0':
			session = shopify.Session(self.url, API_VERSION, self.password)
			shopify.ShopifyResource.activate_session(session)
			if not self.location_id:
				self.location_id = shopify.Shop.current().primary_location_id
			location_id = shopify.Shop.current().primary_location_id
			_logger.info("__enter__====================location_id:%r",location_id)
		else:
			shopify.ShopifyResource.set_user(self.api_key)
			shopify.ShopifyResource.set_password(self.password)
			shopify.ShopifyResource.set_site(self.url)
			if not self.location_id:
				self.location_id = shopify.Shop.current().primary_location_id
		return self

	def __exit__(self,exc_type,exc_value,exc_traceback):
		del self

	def ensure_response(self,obj,method,*args,**kwargs):
		if method in ['save','destroy']:
			request = getattr(obj,method)
			response = request()
			api_call_count = int(
				shopify.ShopifyResource.connection.response.headers.get(
					'X-Shopify-Shop-Api-Call-Limit'
				).split('/')[0]
			)
			if api_call_count >= 35:
				sleep(float(15))
				response = request()
		else:
			if 'next_url' in kwargs:
				kwargs = {'from_': kwargs['next_url']}
			request = getattr(getattr(shopify,obj),method)
			response = request(*args,**kwargs)
			api_call_count = int(
				shopify.ShopifyResource.connection.response.headers.get(
					'X-Shopify-Shop-Api-Call-Limit'
				).split('/')[0]
			)
			if api_call_count >= 35:
				sleep(float(15))
				response = request(*args,**kwargs)
		return response

	def pre_get(self,kw):
		options = {}
		if kw.get('filter_type') == 'data_range':
			updated_at_min = kw.get('updated_at_min')
			updated_at_max = kw.get('updated_at_max')
			if updated_at_min:
				options['updated_at_min'] = updated_at_min
			if updated_at_max:
				options['updated_at_max'] = updated_at_max
		elif kw.get('filter_type') == 'since_id':
			options['since_id'] = kw.get('last_id') or kw.get('since_id') or 0
		if 'limit' in kw:
			options['limit'] = min(kw['limit'],kw['page_size'])
		else:
			options['limit'] = kw['page_size']
		if 'next_url' in kw:
			options['next_url'] = kw['next_url']
		return options

	def post_get(self,kw):
		kw['location_id'] = self.location_id
		if kw.get('filter_type') == 'since_id' and 'limit' in kw:
			limit = kw['limit']
			kw['limit'] = limit-min(limit,kw.get('page_size'))
		return kw

	def get_categories(self,**kw):
		collection_data_list = []
		if kw.get('object_id'):
			collection = self.ensure_response('CustomCollection','find',kw.get('object_id'))
			collection_data_list.append(self.process_collection(collection))
		else:
			options = self.pre_get(kw)
			if options.get('limit'):
				collections = self.ensure_response('CustomCollection','find',**options)
				for collection in collections:
					collection_data_list.append(self.process_collection(collection))
				if collections.has_next_page():
					kw['next_url'] = collections.next_page_url
		return collection_data_list,self.post_get(kw)

	def process_collection(self,collection):
		return {
			'channel_id' : self.id,
			'store_id'   : collection.id,
			'name'       : collection.title,
			'description': collection.body_html
		}

	def get_partners(self,**kw):
		customer_data_list = []
		if kw.get('object_id'):
			customer = self.ensure_response('Customer','find',kw.get('object_id'))
			customer_data_list.append(self.process_customer(customer))
		else:
			options = self.pre_get(kw)
			if options.get('limit'):
				customers = self.ensure_response('Customer','find',**options)
				for customer in customers:
					customer_data_list.append(self.process_customer(customer))
				if customers.has_next_page():
					kw['next_url'] = customers.next_page_url
				if customers:
					kw['last_updated'] = customer.updated_at
		return customer_data_list,self.post_get(kw)

	def process_customer(self,customer):
		name = customer.first_name or ''
		if name:
			name = name + ' '
		name += customer.last_name or ''
		customer_data = {
			'channel_id': self.id,
			'store_id'  : customer.id,
			'name'      : name or customer.email,
			'email'     : customer.email,
			'mobile'    : customer.phone
		}
		if customer.addresses:
			temp_address = self.process_address(customer.default_address,type='customer')
			address_data_list = [temp_address]
			for address in customer.addresses:
				if address.id != customer.default_address.id:
					temp_address = self.process_address(address,type='customer')
					temp_address.update(
						{
							'channel_id': self.id,
							'parent_id' : address.customer_id,
							'store_id'  : address.id,
						}
					)
					address_data_list.append(temp_address)
			customer_data['contacts'] = address_data_list
		return customer_data

	def process_address(self,address,type=False):
		address_data = {
			'name'        : address.name or False,
			'street'      : address.address1 or False,
			'street2'     : address.address2 or False,
			'city'        : address.city or False,
			'state_code'  : address.province_code or False,
			'country_code': address.country_code or False,
			'zip'         : address.zip or False,
			'phone'       : address.phone or False,
		}
		if type == 'customer':
			address_data.update(
				channel_id = self.id,
				parent_id = address.customer_id,
				store_id = address.id,
				type = 'invoice',
			)
		return address_data

	def get_products(self,**kw):
		product_data_list = []
		if kw.get('object_id'):
			product = self.ensure_response('Product','find',kw.get('object_id'))
			product_data_list.append(self.process_product(product))
		else:
			options = self.pre_get(kw)
			if options.get('limit'):
				products = self.ensure_response('Product','find',**options)
				for product in products:
					product_data_list.append(self.process_product(product))
				if products.has_next_page():
					kw['next_url'] = products.next_page_url
				if products:
					kw['last_updated'] = product.updated_at
		return product_data_list,self.post_get(kw)

	def process_product(self,product):
		product_data = {
			'channel_id'      : self.id,
			'store_id'        : product.id,
			'name'            : product.title,
		}
		if product.body_html:
			product_data['description_sale'] = sub('<.*?>','',product.body_html)
		attributes = self.process_attribute(product.options)

		variant_data_list = []
		for variant in product.variants:
			variant_data_list.append(self.process_variant(variant,attributes))

		if len(variant_data_list) == 1:
			product_data['default_code'] = variant_data_list[0].get('default_code')
			product_data['barcode']      = variant_data_list[0].get('barcode')
			product_data['list_price']   = variant_data_list[0].get('list_price')

		product_data['variants'] = variant_data_list

		if product.image:
			product_data['image_url'] = product.image.src

		collections = self.ensure_response('CustomCollection','find',product_id=product.id)
		product_data['extra_categ_ids'] = ','.join(map(lambda x:str(x.id),collections))
		return product_data

	def process_attribute(self,options):
		attributes = {}
		for option in options:
			for value in option.values:
				attributes[value] = option.name
		return attributes

	def process_variant(self,variant,attributes):
		variant_data = {
			'channel_id'  : self.id,
			'store_id'    : variant.id,
			'default_code': variant.sku,
			'barcode'     : variant.barcode,
			'list_price'  : variant.price,
			'weight'      : variant.weight,
			'weight_unit' : variant.weight_unit,
		}

		attribute_line = []
		if variant.option1 and variant.option1 !='Default Title':
			attribute_line.append(
				{
					'name' : attributes.get(variant.option1),
					'value': variant.option1
				}
			)
			if variant.option2:
				attribute_line.append(
					{
						'name' : attributes.get(variant.option2),
						'value': variant.option2
					}
				)
				if variant.option3:
					attribute_line.append(
						{
							'name' : attributes.get(variant.option3),
							'value': variant.option3
						}
					)
		variant_data['name_value']    = attribute_line
		variant_data['qty_available'] = self.ensure_response(
			'InventoryLevel',
			'connect',
			self.location_id,
			variant.inventory_item_id,
		).available
		return variant_data

	def get_orders(self,**kw):
		order_data_list = []
		if kw.get('object_id'):
			order = self.ensure_response('Order','find',kw.get('object_id'))
			if order.financial_status != 'refunded':
				order_data_list.append(self.process_order(order))
		else:
			options = self.pre_get(kw)
			if options.get('limit'):
				orders = self.ensure_response('Order','find',status='any',**options)
				for order in orders:
					if order.financial_status != 'refunded':
						order_data_list.append(self.process_order(order))
			if orders.has_next_page():
				kw['next_url'] = orders.next_page_url
			if orders:
				kw['last_updated'] = order.updated_at
		return order_data_list,self.post_get(kw)

	def process_order(self,order):
		order_data = {
			'channel_id'       : self.id,
			'store_id'         : order.id,
			'name'             : order.name,
			'currency'         : order.currency,
			'date_order'       : order.created_at,
			'confirmation_date': order.updated_at,
			'line_type'        : 'multi'
		}

		if order.fulfillment_status == 'fulfilled':
			order_data['order_state'] = 'Done'
		elif order.cancelled_at:
			order_data['order_state'] = 'Cancelled'
		elif order.financial_status == 'paid':
			order_data['order_state'] = 'Paid'
		else:
			order_data['order_state'] = 'Sale'

		if order.payment_gateway_names:
			order_data.update(payment_method = order.payment_gateway_names[0])
		elif order.financial_status == 'paid':
			order_data.update(payment_method = 'Paid by Customer')

		if order.shipping_lines:
			order_data.update(carrier_id = order.shipping_lines[0].title)

		if order.attributes.get('customer'):
			order_data.update(
				{
					'partner_id'       : order.customer.id,
					'customer_name'    : order.customer.first_name+' '+order.customer.last_name,
					'customer_email'   : order.customer.email,
					'customer_mobile'  : order.customer.phone,
					'customer_phone'   : order.customer.attributes.get('default_address') and order.customer.default_address.phone,
				}
			)

			try:
				invoice_address = self.process_address(order.billing_address,type='order')
			except AttributeError:
				invoice_address= None

			try:
				shipping_address = self.process_address(order.shipping_address,type='order')
			except AttributeError:
				shipping_address = None

			same_address = invoice_address == shipping_address
			if invoice_address:
				invoice_address.update(
					{
						'partner_id': order.customer.id,
						'email'     : order.email
					}
				)
				order_data.update({'invoice_'+k:v for k,v in invoice_address.items()})
			if shipping_address and not same_address:
				shipping_address.update(
					{
						'partner_id': order.customer.id,
						'email'     : order.email
					}
				)
				order_data.update({'shipping_'+k:v for k,v in shipping_address.items()})
			if invoice_address and shipping_address:
				order_data.update(same_shipping_billing = same_address)

		order_lines = [(5,0)]
		for line in order.line_items:
			order_line_data = {
				'line_name'                : line.title,
				'line_product_id'          : line.product_id,
				'line_variant_ids'         : line.variant_id,
				'line_price_unit'          : line.price,
				'line_product_uom_qty'     : line.quantity,
				'line_product_default_code': line.sku,
				'line_taxes'               : self.process_tax(line,order.taxes_included),
			}
			order_lines.append((0,0,order_line_data))

		for line in order.shipping_lines:
			delivery_line_data = {
				'line_name'                : 'Delivery: {}'.format(line.title),
				'line_product_id'          : line.id,
				'line_price_unit'          : line.price,
				'line_product_uom_qty'     : 1,
				'line_product_default_code': line.code,
				'line_taxes'               : self.process_tax(line,order.taxes_included),
				'line_source'              : 'delivery',
			}
			order_lines.append((0,0,delivery_line_data))

		for line in order.discount_codes:
			discount_line_data = {
				'line_name'                : 'Discount: {}'.format(line.code),
				'line_product_id'          : line.code,
				'line_price_unit'          : line.amount,
				'line_product_uom_qty'     : 1,
				'line_product_default_code': line.code,
				'line_taxes'               :  self.process_tax(order.line_items[0],order.taxes_included),
				'line_source'              : 'discount',
			}
			order_lines.append((0,0,discount_line_data))

		order_data['line_ids'] = order_lines
		return order_data

	def process_tax(self,order_line,taxes_included=False,tax_type='percent'):
		return [
			{
				'included_in_price': taxes_included,
				'name'             : tax.title,
				'rate'             : tax.rate*100,
				'tax_type'         : 'percent'
			} for tax in order_line.tax_lines
		]

	def post_category(self,record):
		collection        = shopify.CustomCollection()
		collection.title  = record.name
		collection.handle = record.complete_name
		if self.ensure_response(collection,'save'):
			return True,collection
		else:
			_logger.error(collection.errors.errors)
			return False,collection

	def put_category(self,record,remote_id):
		collection       = shopify.CustomCollection({'id':remote_id})
		collection.title = record.name
		if self.ensure_response(collection,'save'):
			return True,collection
		else:
			_logger.error(collection.errors.errors)
			return False,collection

	def post_product(self,record):
		product           = shopify.Product()
		product.title     = record.name
		product.handle    = record.default_code or record.name
		product.body_html = record.description_sale or record.description_purchase or ''

		if record.attribute_line_ids:
			product.options = [
				{
					'name': attribute_line.attribute_id.display_name
				} for attribute_line in record.attribute_line_ids
			]

		product.variants = []
		for local_variant in record.product_variant_ids:
			variant = {
				'price'               : local_variant.lst_price,
				'sku'                 : local_variant.default_code or '',
				'barcode'             : local_variant.barcode or '',
				'weight'              : local_variant.weight,
				'weight_unit'         : local_variant.weight_uom_name,
				'inventory_management': 'shopify',
			}

			if record.attribute_line_ids:
				option_count = len(product.options)
				if option_count > 0:
					variant.update(
						option1 = local_variant.product_template_attribute_value_ids.filtered(
							lambda self:product.options[0].get('name') in self.display_name
						).name
					)
					if option_count > 1:
						variant.update(
							option2 = local_variant.product_template_attribute_value_ids.filtered(
								lambda self:product.options[1].get('name') in self.display_name
							).name
						)
						if option_count > 2:
							variant.update(
								option2 = local_variant.product_template_attribute_value_ids.filtered(
									lambda self:product.options[2].get('name') in self.display_name
								).name
							)
			variant = shopify.Variant(variant)
			product.variants.append(variant)
		if self.ensure_response(product,'save'):
			for local_variant,remote_variant in zip(record.product_variant_ids,product.variants):
				self.put_variant(local_variant,remote_variant.id,product)
			return True,product
		else:
			_logger.error(product.errors.errors)
			return False,product

	def put_product(self,record,remote_id):
		product           = shopify.Product.find(remote_id)
		product.title     = record.name
		product.handle    = record.default_code or record.name
		product.body_html = record.description_sale or record.description_purchase or ''
		product.images    = []

		if record.attribute_line_ids:
			product.options = [
				{
					'name': attribute_line.attribute_id.display_name
				} for attribute_line in record.attribute_line_ids
			]

		if self.ensure_response(product,'save'):
			return True,product
		else:
			_logger.error(product.errors.errors)
			return False,product

	def put_variant(self,record,remote_id,product):
		variant                      = shopify.Variant({'id':remote_id})
		variant.product_id           = product.id
		variant.price                = round(self.pricelist_id._get_product_price(record, quantity=1),2)
		variant.sku                  = record.default_code or ''
		variant.barcode              = record.barcode or ''
		variant.weight               = record.weight
		variant.weight_unit          = record.weight_uom_name
		variant.inventory_management = 'shopify'

		if record.image_1920:
			image            = shopify.Image()
			image.alt        = product.handle
			image.attachment = record.image_1920.decode('utf-8')
			image.product_id = product.id
			if self.ensure_response(image,'save'):
				variant.image_id = image.id
			else:
				_logger.error(image.errors.errors)

		if record.product_template_attribute_value_ids:
			option_count = len(product.options)
			if option_count > 0:
				variant.option1 = record.product_template_attribute_value_ids.filtered(
					lambda self:product.options[0].name in self.display_name
				).name
				if option_count > 1:
					variant.option2 = record.product_template_attribute_value_ids.filtered(
						lambda self:product.options[1].name in self.display_name
					).name
					if option_count > 2:
						variant.option3 = record.product_template_attribute_value_ids.filtered(
							lambda self:product.options[2].name in self.display_name
						).name

		if self.ensure_response(variant,'save'):
			return True,variant
		else:
			_logger.error(variant.errors.errors)
			return False,variant

	def set_quantity(self,variant,qty=0):
		if isinstance(variant, (int, str)):
			variant = self.ensure_response('Variant','find',variant)
		return bool(
			self.ensure_response(
				'InventoryLevel',
				'set',
				self.location_id,
				variant.inventory_item_id,
				int(qty),
			)
		)

	def get_collects(self,product_id):
		res = self.ensure_response('Collect','find',product_id=product_id)
		return res

	def post_collects(self,product_id,collection_id):
		collect = shopify.Collect(
			{
				'product_id': product_id,
				'collection_id': collection_id,
			}
		)
		if not self.ensure_response(collect,'save'):
			_logger.error(collect.errors.errors)

	def delete_collect(self,collect):
		self.ensure_response(collect,'destroy')

	def mark_order_paid(self, order_id):
		transaction = self.ensure_response('Transaction','find',order_id=order_id)
		transaction = transaction[0]
		transaction = shopify.Transaction(
			{
				'parent_id': transaction.id,
				'order_id' : order_id,
				'kind'     : 'capture',
				'gateway'  : transaction.gateway,
				'amount'   : transaction.amount,
				'status'   : 'success',
				'currency' : transaction.currency
			}
		)
		if not self.ensure_response(transaction,'save'):
			_logger.error(transaction.errors.errors)

	def mark_order_fulfill(self, order_id, sale_order):
		fulfillment = {
			"location_id"    : self.location_id,
			"tracking_number": sale_order.carrier_tracking_ref,
			'notify_customer': True,
		}

		vals = {
			'order_id'   : order_id,
			'location_id': self.location_id,
			"tracking_number": sale_order.carrier_tracking_ref,
			'fulfillment': fulfillment,
		}

		fulfillment = shopify.Fulfillment(vals)
		if not self.ensure_response(fulfillment,'save'):
			_logger.error(fulfillment.errors.errors)

	def mark_order_refund(self, invoice, order_id):
		transaction = self.ensure_response('Transaction','find',order_id=order_id)
		transaction = transaction[0]
		order = self.ensure_response('Order','find',order_id)
		refund_line_items = []
		for line_item in order.line_items:
			refund_line_items.append(
				{
					'line_item_id': line_item.id,
					'quantity'    : line_item.quantity,
					'restock_type': 'return',
					'location_id' : self.location_id,
				}
			)

		refund = shopify.Refund(
			{
				'order_id'         : order_id,
				'refund_line_items': refund_line_items,
				'refund'           : {
					'amount'  : transaction.amount,
					'shipping': {'full_refund' : True},
					'currency': transaction.currency
				},
				'transactions': [
					{
						'parent_id': transaction.id,
						'order_id' : order_id,
						'kind'     : 'refund',
						'gateway'  : transaction.gateway,
						'amount'   : transaction.amount,
						'status'   : 'success',
					}
				],
			}
		)
		if not self.ensure_response(refund,'save'):
			_logger.error(refund.errors.errors)
