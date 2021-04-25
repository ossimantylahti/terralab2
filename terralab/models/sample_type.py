# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)

class SampleType(models.Model):
    _name = 'terralab.sampletype'
    _inherit = ['mail.thread']
    _description = 'TerraLab Sample Type'

    submitted_samples = fields.One2many('terralab.submittedsample', 'sample_type', 'Submitted Samples', track_visibility='onchange') # There are many Submitted Samples for one Sample Type
    test_types = fields.One2many('terralab.testtype', 'sample_type', 'Test Types', track_visibility='onchange') # There are many Test Types for one Sample Type
    name = fields.Char(track_visibility='onchange')
