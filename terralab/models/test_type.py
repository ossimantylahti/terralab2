# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)

class TestType(models.Model):
    _name = 'terralab.testtype'
    _inherit = ['mail.thread']
    _description = 'TerraLab Test'

    test_variable_types = fields.One2many('terralab.testvariabletype', 'test_type', 'Test Variable Types', track_visibility='onchange') # Test Types have a number of Test Variable Types
    sample_types = fields.Many2many('terralab.sampletype', track_visibility='onchange')
    spreadsheet = fields.Many2one('terralab.spreadsheet', 'Spreadsheet', track_visibility='onchange') # Spreadsheet used to calculate test results (and source of import)
    default_code = fields.Char(track_visibility='onchange')
    name = fields.Char(track_visibility='onchange')
    test_products = fields.Many2many('product.template', track_visibility='onchange')
    test_result_uom_name = fields.Char(track_visibility='onchange')
