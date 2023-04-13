# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################

from odoo import models

class StockMove(models.Model):
	_inherit = 'stock.move'

	def multichannel_sync_quantity(self,pick_details):
		channel_list = self._context.get('channel_list',[])
		channel_list.append('shopify')
		return super(
			StockMove,self.with_context(channel_list = channel_list)
		).multichannel_sync_quantity(pick_details)
