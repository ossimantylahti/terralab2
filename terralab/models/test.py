# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)

class Test(models.Model):
    _name = 'terralab.test'
    _inherit = ['mail.thread']
    _description = 'TerraLab Test'

    test_variables = fields.One2many('terralab.testvariable', 'test', 'Test Variables', track_visibility='onchange') # Tests have a number of Test Variables
    sample = fields.Many2one('terralab.sample', 'Sample', track_visibility='onchange') # Tests have a Sample
    spreadsheet = fields.Many2one('terralab.spreadsheet', 'Spreadsheet', track_visibility='onchange') # Spreadsheet used to calculate test results
    name = fields.Char(track_visibility='onchange')
    spreadsheet_result_ref = fields.Char(track_visibility='onchange') # Spreadsheet result reference, Sheet!A1
    test_products = fields.Many2many('product.template', track_visibility='onchange')
    test_result_uom = fields.Many2one('uom.uom', track_visibility='onchange')
