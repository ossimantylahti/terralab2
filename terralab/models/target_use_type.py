# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)

class TargetUseType(models.Model):
    _name = 'terralab.targetusetype'
    _inherit = ['mail.thread']
    _description = 'TerraLab Target Use Type'

    spreadsheet = fields.Many2one('terralab.spreadsheet', 'Spreadsheet', track_visibility='onchange') # Spreadsheet source of import
    submitted_target_uses = fields.One2many('terralab.submittedtargetuse', 'target_use_type', 'Submitted Target Uses', track_visibility='onchange')
    default_code = fields.Char(track_visibility='onchange')
    name = fields.Char(translate=True, track_visibility='onchange')
