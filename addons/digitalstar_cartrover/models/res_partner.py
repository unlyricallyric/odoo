from odoo import fields, models, api
from datetime import datetime, timedelta

class ResPartner(models.Model):
    _inherit = 'res.partner'

    buyer_email = fields.Char(help="The buyer email")
    buyer_name = fields.Char(help="The buyer name")
    #
    # @api.model
    # def _archive_old_wayfair_partners(self):
    #     date_to_delete = datetime.today() - timedelta(days=365)
    #     target_partners = self.search([
    #         ('wayfair_buyer_name', '!=', ''),
    #         ('create_date', '<=', date_to_delete),
    #         ('name', 'not ilike', 'Wayfair Customer #%')
    #         ])
    #     if target_partners:
    #         for partner in target_partners:
    #             partner.name = 'Wayfair Customer #' + str(partner.id)
    #         print ('++++++++++++++++++++ Success: Archived a total number of {} wayfair contacts ++++++++++++++++++++'.format(len(target_partners)))
    #     else:
    #         print ('++++++++++++++++++++ No old wayfair contacts need to be archived ++++++++++++++++++++')