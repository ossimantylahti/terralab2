# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)

class TestVariableType(models.Model):
    _name = 'terralab.testvariabletype'
    _inherit = ['mail.thread']
    _description = 'TerraLab Test Variable Type'

    spreadsheet = fields.Many2one('terralab.spreadsheet', 'Spreadsheet', track_visibility='onchange') # Spreadsheet source of import
    test_type = fields.Many2one('terralab.testtype', 'Test Type', track_visibility='onchange') # Test Variable Types are attached to a specific Test Type
    submitted_test_variables = fields.One2many('terralab.submittedtestvariable', 'test_variable_type', 'Submitted Test Variables', track_visibility='onchange') # There are many Submitted Test Variables for one Test Variable Type
    num = fields.Integer(track_visibility='onchange')
    name = fields.Char(track_visibility='onchange')
