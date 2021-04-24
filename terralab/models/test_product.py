# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)

# This attaches Tests to Odoo Products
class TestProduct(models.Model):
    _name = 'product.template'
    _inherit = ['mail.thread']
    _inherit = 'product.template'

    terralab_tests_count = fields.Integer(compute='_compute_terralab_tests_count', store=True, track_visibility='onchange')
    terralab_tests = fields.Many2many('terralab.test', track_visibility='onchange')

    @api.depends('terralab_tests', 'bom_ids', 'bom_ids.bom_line_ids', 'bom_ids.bom_line_ids.product_id')
    def _compute_terralab_tests_count(self):
        for item in self:
            logger.info('CHECKING TERRALAB TESTS %s %s %s' %(item.bom_count, item.bom_ids, item.bom_line_ids))
            terralab_tests_count = 0
            if hasattr(item, 'terralab_tests'):
                for terralab_test in item.terralab_tests:
                    logger.info('- TERRALAB TEST %s' % (terralab_test))
                    terralab_tests_count += 1
            if hasattr(item, 'bom_ids'):
                for bom_id in item.bom_ids:
                    logger.info('- BOM %s' % (dir(bom_id)))
                    if hasattr(bom_id, 'bom_line_ids'):
                        for bom_line_id in bom_id.bom_line_ids:
                            logger.info('- BOM LINE %s' % (bom_line_id))
                            logger.info('  - PRODUCT %s' % (bom_line_id.product_id))
                            if bom_line_id.product_id and hasattr(bom_line_id.product_id, 'terralab_tests'):
                                for terralab_test in bom_line_id.product_id.terralab_tests:
                                    logger.info('   - TERRALAB TEST %s' % (terralab_test))
                                    terralab_tests_count += 1
            item.terralab_tests_count = terralab_tests_count
