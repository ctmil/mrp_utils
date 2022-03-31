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
        if (not product_from):
            raise ValidationError(_('Products missing'))
        for bom_line in self.bom_line_ids:
            if not bom_line.product_id.bom_ids:
                if bom_line.product_id.id == product_from.id:
                    if product_to:
                        bom_line.product_id = product_to.id
                    else:
                        bom_line.unlink()
            else:
                if bom_line.product_id.source_product_id.id == product_from.id:
                    if product_to:
                        bom_line.product_id = product_to.id
                    else:
                        bom_line.unlink()
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

    # Duplicate methods


    def _duplicate_bom(self, change_id = None):
        for bom_line in self.bom_line_ids:
            if bom_line.product_id.bom_ids:
                change = self.env['mrp.bom.change'].browse(change_id)
                suffix = ' (' + change.name + ')'
                bom = bom_line.product_id.bom_ids[0]
                product_tmpl = bom_line.product_id.product_tmpl_id
                new_product_tmpl = product_tmpl.copy(default = {
                    'name': str(product_tmpl.name), 
                    'change_id': change_id,
                    'default_code': suffix + ' ' + str(product_tmpl.name),
                    'source_product_tmpl_id': product_tmpl.id,
                    })
                new_product = new_product_tmpl.product_variant_ids[0]
                new_product.change_id = change_id
                new_product.source_product_id = bom_line.product_id
                new_bom = bom.copy(default={'code': str(bom.code) + suffix,
                    'product_tmpl_id': new_product_tmpl.id,
                    'change_id': change_id,
                    'source_bom_id': bom.id,
                    })
                bom_line.product_id = new_product.id
                new_bom._duplicate_bom(change_id)
        return True



    def duplicate_bom(self, change_id = None):
        self.ensure_one()
        product = self.product_tmpl_id
        change = self.env['mrp.bom.change'].browse(change_id)
        suffix = ' (' + change.name + ')'
        default_code = suffix + ' ' + product.name
        new_product_tmpl = product.copy({
            'name': str(product.name),
            'default_code': default_code,
            'change_id': change_id,
            'source_product_tmpl_id': product.id,
            })
        new_bom = self.copy(default={
            'code': self.code and str(self.code) + suffix,
            'product_tmpl_id': new_product_tmpl.id,
            'change_id': change_id,
            'source_bom_id': self.id,
            })
        change.created_main_bom_id = new_bom.id
        new_bom._duplicate_bom(change_id)


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
    change_id = fields.Many2one('mrp.bom.change')
    source_bom_id = fields.Many2one('mrp.bom',string='Source BoM')

class MrpBomChange(models.Model):
    _name = 'mrp.bom.change'
    _description = 'Records changes to BoMs'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    def btn_replace(self):
        self.ensure_one()
        if not self.bom_id:
            raise ValidationError(_('You have to select BoM'))
        if not self.name:
            raise ValidationError(_('You have to enter a name'))
        if not self.line_ids:
            raise ValidationError(_('You have to enter replacement products'))
        bom_id = self.bom_id
        bom_id.duplicate_bom(change_id = self.id)
        if self.line_ids:
            for line in self.line_ids:
                if line.product_from:
                    new_bom = self.created_main_bom_id
                    new_bom._replace_bom_products(line.product_from,line.product_to)
        self.state = 'done'


    @api.onchange('bom_id')
    def onchange_bom_id(self):
        if self.bom_id:
            self.product_tmpl_id = self.bom_id.product_tmpl_id.id

    name = fields.Char('Version', readonly=True, states={'draft': [('readonly', False)]})
    date = fields.Date('Date',default=fields.Date.today(), readonly=True, states={'draft': [('readonly', False)]})
    bom_id = fields.Many2one('mrp.bom',string='Bill of Material', readonly=True, states={'draft': [('readonly', False)]})
    product_tmpl_id = fields.Many2one('product.template',string='Product', readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection(selection=[('draft','Draft'),('done','Done')],default='draft')
    line_ids = fields.One2many(comodel_name='mrp.bom.change.line',inverse_name="change_id",readonly=True,states={'draft': [('readonly', False)]})
    bom_ids = fields.One2many(comodel_name='mrp.bom',inverse_name="change_id",string="Created BoMs")
    created_main_bom_id = fields.Many2one('mrp.bom',string='Main BoM created')
    product_tmpl_ids = fields.One2many(comodel_name='product.template',inverse_name="change_id",string="Created Products")

class MrpBomChangeLine(models.Model):
    _name = 'mrp.bom.change.line'
    _description = 'MRP Bom change lines'

    change_id = fields.Many2one('mrp.bom.change')
    product_from = fields.Many2one('product.product','Product from')
    product_to = fields.Many2one('product.product','Product to')

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    change_id = fields.Many2one('mrp.bom.change')
    source_product_id = fields.Many2one('product.product',string='Source Product')
    source_product_tmpl_id = fields.Many2one('product.template',string='Source Product Template')

class ProductProduct(models.Model):
    _inherit = 'product.product'

    change_id = fields.Many2one('mrp.bom.change')
    source_product_id = fields.Many2one('product.product',string='Source Product')

