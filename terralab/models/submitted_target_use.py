# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)

class SubmittedTargetUse(models.Model):
    _name = 'terralab.submittedtargetuse'
    _inherit = ['mail.thread']
    _description = 'TerraLab Submitted Target Use'

    spreadsheet = fields.Many2one('terralab.spreadsheet', 'Spreadsheet', track_visibility='onchange') # Spreadsheet source of import
    target_use_type = fields.Many2one('terralab.targetusetype', 'Target Use Type', track_visibility='onchange') # Submitted Target Use is of a Target Use Type
    submitted_samples = fields.One2many('terralab.submittedsample', 'sample_type', 'Submitted Samples', track_visibility='onchange') # There are many Submitted Samples for one Sample Type
    test_type = fields.Many2one('terralab.testtype', 'Test Type', track_visibility='onchange') # Submitted Target Use is connected to a Test Type
    threshold_1 = fields.Float(track_visibility='onchange')
    threshold_2 = fields.Float(track_visibility='onchange')
    threshold_3 = fields.Float(track_visibility='onchange')
    threshold_4 = fields.Float(track_visibility='onchange')
    threshold_5 = fields.Float(track_visibility='onchange')
    name = fields.Char(compute='_get_name', store=True, track_visibility='onchange')

    @api.depends('target_use_type', 'test_type')
    def _get_name(self):
        for item in self:
            if item.target_use_type and item.test_type:
                item.name = '%s (%s)' % (item.target_use_type.name, item.test_type.name)
            else:
                item.name = ''
