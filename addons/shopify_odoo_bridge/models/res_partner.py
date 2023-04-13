# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from odoo import models


class ResPartner(models.Model):
	_inherit = 'res.partner'

	def _fields_sync(self, values):
		""" Sync commercial fields and address fields from company and to children after create/update,
		just as if those were all modeled as fields.related to the parent """
		if self._context.get('channel') == 'shopify':
			# 1a. Commercial fields: sync if parent changed
			if values.get('parent_id'):
				self._commercial_sync_from_company()
			return
		return super()._fields_sync(values)
