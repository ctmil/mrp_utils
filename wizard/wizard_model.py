from odoo import fields,models, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)



class BomReplaceWizard(models.TransientModel):
    _name = 'bom.replace.wizard'

    bom_id = fields.Many2one('mrp.bom',string='Bill of Materials')
    product_from = fields.Many2one('product.product',string='Old product')
    product_to = fields.Many2one('product.product',string='New product')

    def btn_confirm(self):
        if not self.product_from or not self.product_to:
            raise ValidationError(_('You must supply products'))
        if self.product_from.id == self.product_to.id:
            raise ValidationError(_('Products have to be different'))
        bom_id = self.bom_id
        bom_id.replace_bom_products(self.product_from,self.product_to)
