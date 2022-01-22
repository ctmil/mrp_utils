##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api, _
import logging
from odoo.exceptions import UserError, ValidationError
import odoo.tools as tools
import os
import hashlib
import time
import sys
import traceback

_logger = logging.getLogger(__name__)


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    # Demo methods

    def _get_bom_products(self, value=0):
        for bom_line in self.bom_line_ids:
            if not bom_line.product_id.bom_ids:
                value = value + bom_line.product_id.id
            else:
                new_bom = bom_line.product_id.bom_ids[0]
                value = new_bom._get_bom_products(value)
        return value

    def get_bom_products(self):
        self.res_get_bom_products = self._get_bom_products()

    # Replace methods 

    def _replace_bom_products(self, product_from = None, product_to = None):
        if (not product_from) or (not product_to):
            raise ValidationError(_('Products missing'))
        for bom_line in self.bom_line_ids:
            if not bom_line.product_id.bom_ids:
                if bom_line.product_id.id == product_from.id:
                    bom_line.product_id = product_to.id
            else:
                if bom_line.product_id.id == product_from.id:
                    bom_line.product_id = product_to.id
                else:
                    new_bom = bom_line.product_id.bom_ids[0]
                    value = new_bom._replace_bom_products(product_from,product_to)
        return True

    def replace_bom_products(self,product_from=None,product_to=None):
        self.ensure_one()
        if not product_from or not product_to:
            raise ValidationError(_('Products missing'))
        self._replace_bom_products(
                product_from=product_from,
                product_to=product_to)

    def replace_components(self):
        self.ensure_one()
        if not self.bom_line_ids:
            raise ValidationError(_('No lines in current BoM'))
        vals = {
                'bom_id': self.id,
                }
        wizard_id = self.env['bom.replace.wizard'].create(vals)
        return {
            'name': _('Replace components'),
            'res_model': 'bom.replace.wizard',
            'view_mode': 'form',
            'res_id': wizard_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


    res_get_bom_products = fields.Integer('_get_bom_products')
