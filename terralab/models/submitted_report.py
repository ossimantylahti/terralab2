# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)

class SubmittedReport(models.Model):
    _name = 'terralab.submittedreport'
    _inherit = ['mail.thread']
    _description = 'TerraLab Submitted Report'

    order = fields.Many2one('sale.order', 'Order', track_visibility='onchange') # A Submitted Report is attached to a specific Order
    report_type = fields.Many2one('terralab.reporttype', 'Report Type', track_visibility='onchange') # Submitted Report is a specific Report Type
    generated_at = fields.Datetime(track_visibility='onchange') # Report generation time
    print_count = fields.Integer(track_visibility='onchange')

    def name_get(self):
        return [(report.id, '%s %s %s %s' % (report.order.name, report.report_type.name, report.report_type.report_action, report.generated_at)) for report in self]

    # Report view action: Print Report
    def action_terralab_print(self):
        self.ensure_one()
        if self.report_type and self.report_type.report_action:
            self.write({
                'print_count': self.print_count + 1,
            })
            return self.env.ref('%s' % (self.report_type.report_action)).report_action(self)
