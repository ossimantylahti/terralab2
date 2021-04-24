# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)

class Report(models.Model):
    _name = 'terralab.report'
    _inherit = ['mail.thread']
    _description = 'TerraLab Report'

    order = fields.Many2one('sale.order', 'Order', track_visibility='onchange') # A Report is attached to a specific Order
    generated_at = fields.Datetime(track_visibility='onchange') # Report generation time
    print_count = fields.Integer(track_visibility='onchange')
    report_name = fields.Char(default='terralab_test_report')

    def name_get(self):
        return [(report.id, '%s %s' % (report.order.name, report.generated_at)) for report in self]

    # Report view action: Print Report
    def action_terralab_print(self):
        self.ensure_one()
        if self.report_name:
            self.write({
                'print_count': self.print_count + 1,
            })
            return self.env.ref('terralab.action_print_%s' % (self.report_name)).report_action(self)
