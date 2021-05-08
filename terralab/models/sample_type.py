# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)

class SampleType(models.Model):
    _name = 'terralab.sampletype'
    _inherit = ['mail.thread']
    _description = 'TerraLab Sample Type'

    submitted_samples = fields.One2many('terralab.submittedsample', 'sample_type', 'Submitted Samples', track_visibility='onchange') # There are many Submitted Samples for one Sample Type
    #test_types = fields.One2many('terralab.testtype', 'sample_type', 'Test Types', track_visibility='onchange') # There are many Test Types for one Sample Type
    test_types = fields.Many2many('terralab.testtype', track_visibility='onchange')
    spreadsheet = fields.Many2one('terralab.spreadsheet', 'Spreadsheet', track_visibility='onchange') # Spreadsheet source of import
    name = fields.Char(translate=True, track_visibility='onchange')
    default_code = fields.Char(track_visibility='onchange')
