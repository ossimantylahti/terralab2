# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)

class TestVariable(models.Model):
    _name = 'terralab.testvariable'
    _inherit = ['mail.thread']
    _description = 'TerraLab Test Variable'

    test = fields.Many2one('terralab.test', 'Test', track_visibility='onchange') # Test Variables are attached to a specific Test
    submitted_test_variables = fields.One2many('terralab.submittedtestvariable', 'test_variable', 'Submitted Test Variables', track_visibility='onchange') # There are many Submitted TestVariables for one TestVariable
    name = fields.Char(track_visibility='onchange')
    spreadsheet_input_ref = fields.Char(track_visibility='onchange') # Spreadsheet input reference, Sheet!A1
