# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)

# This attaches Tests to Odoo Products
class TestProduct(models.Model):
    _name = 'product.template'
    _inherit = ['mail.thread']
    _inherit = 'product.template'

    terralab_test_types_count = fields.Integer(compute='_compute_terralab_test_types_count', store=True, track_visibility='onchange')
    terralab_test_types = fields.Many2many('terralab.testtype', track_visibility='onchange')
    terralab_spreadsheet = fields.Many2one('terralab.spreadsheet', 'Spreadsheet', track_visibility='onchange') # Spreadsheet source of import

    @api.depends('terralab_test_types', 'bom_ids', 'bom_ids.bom_line_ids', 'bom_ids.bom_line_ids.product_id')
    def _compute_terralab_test_types_count(self):
        for item in self:
            logger.debug('CHECKING TERRALAB TEST TYPES %s %s %s' %(item.bom_count, item.bom_ids, item.bom_line_ids))
            terralab_test_types_count = 0
            if hasattr(item, 'terralab_test_types'):
                for terralab_test_type in item.terralab_test_types:
                    logger.debug('- TERRALAB TEST %s' % (terralab_test_type))
                    terralab_test_types_count += 1
            if hasattr(item, 'bom_ids'):
                for bom_id in item.bom_ids:
                    logger.debug('- BOM %s' % (dir(bom_id)))
                    if hasattr(bom_id, 'bom_line_ids'):
                        for bom_line_id in bom_id.bom_line_ids:
                            logger.debug('- BOM LINE %s' % (bom_line_id))
                            logger.debug('  - PRODUCT %s' % (bom_line_id.product_id))
                            if bom_line_id.product_id and hasattr(bom_line_id.product_id, 'terralab_test_types'):
                                for terralab_test_type in bom_line_id.product_id.terralab_test_types:
                                    logger.debug('   - TERRALAB TEST TYPE %s' % (terralab_test_type))
                                    terralab_test_types_count += 1
            item.terralab_test_types_count = terralab_test_types_count
