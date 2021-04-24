# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)

class Sample(models.Model):
    _name = 'terralab.sample'
    _inherit = ['mail.thread']
    _description = 'TerraLab Sample'

    samples = fields.One2many('terralab.submittedsample', 'sample', 'Submitted Samples', track_visibility='onchange') # There are many Submitted Samples for one Sample
    tests = fields.One2many('terralab.test', 'sample', 'Tests', track_visibility='onchange') # There are many Tests for one Sample
    name = fields.Char(track_visibility='onchange')
