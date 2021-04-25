# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)

class ReportType(models.Model):
    _name = 'terralab.reporttype'
    _inherit = ['mail.thread']
    _description = 'TerraLab Report Type'

    submitted_reports = fields.One2many('terralab.submittedreport', 'report_type', 'Submitted Reports', track_visibility='onchange') # There are many Submitted Reports for one Report Type
    name = fields.Char() # User-friendly name
    report_action = fields.Char(default='terralab.action_print_terralab_test_report') # Specifies which report template to use
