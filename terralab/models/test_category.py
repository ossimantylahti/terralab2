# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)

# This attaches Tests to Odoo Products
class TestCategory(models.Model):
    _name = 'product.category'
    _inherit = ['mail.thread']
    _inherit = 'product.category'

    terralab_default_code = fields.Char()
    terralab_spreadsheet = fields.Many2one('terralab.spreadsheet', 'Spreadsheet', track_visibility='onchange') # Spreadsheet source of import
