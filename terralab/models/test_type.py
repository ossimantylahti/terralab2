# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)

class Test(models.Model):
    _name = 'terralab.testtype'
    _inherit = ['mail.thread']
    _description = 'TerraLab Test'

    test_variable_types = fields.One2many('terralab.testvariabletype', 'test_type', 'Test Variable Types', track_visibility='onchange') # Test Types have a number of Test Variable Types
    sample_type = fields.Many2one('terralab.sampletype', 'Sample Type', track_visibility='onchange') # Test Types have a Sample Type
    spreadsheet = fields.Many2one('terralab.spreadsheet', 'Spreadsheet', track_visibility='onchange') # Spreadsheet used to calculate test results
    name = fields.Char(track_visibility='onchange')
    spreadsheet_result_ref = fields.Char(track_visibility='onchange') # Spreadsheet result reference, Sheet!A1
    test_products = fields.Many2many('product.template', track_visibility='onchange')
    test_result_uom = fields.Many2one('uom.uom', track_visibility='onchange')
