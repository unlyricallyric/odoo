# -*- coding: utf-8 -*-
# Developed by Digital Star.
from odoo import models, fields, api

class Product(models.Model):
    _inherit = "product.product"

    @api.model
    def create(self,vals):
        res = super(Product,self).create(vals)
        if 'weight_configure' in vals and vals['weight_configure']:
            res.product_tmpl_id.update_weight()
            weight_amount = res.product_tmpl_id.weight
            res.weight = weight_amount
        return res

class ProductTemplate(models.Model):
    _inherit = "product.template"

    length = fields.Float('Length',digits='Length')
    height = fields.Float('Height',digits='Height')
    width = fields.Float('Width',digits='Width')
    weight_configure = fields.Float(string="Weight Configuration")
    lenth_configure = fields.Float(string="Lenth Configuration")
    height_configure = fields.Float(string="Height Configuration")
    width_configure = fields.Float(string="Width Configuration")
    volume_uom_id = fields.Many2one('uom.uom',string="Volume UOM",compute="_compute_volume_uom")
    inch_uom_id = fields.Many2one('uom.uom',string="Inch UOM",compute="_compute_inch_uom")

    def _compute_inch_uom(self):
        for obj in self:
            inch_uom_id = self.env['uom.uom'].search([('name','=','in')])
            if inch_uom_id:
                obj.inch_uom_id = inch_uom_id[0].id
            else:
                obj.inch_uom_id = False


    @api.model
    def create(self,vals):
        res = super(ProductTemplate,self).create(vals)
        if 'weight_configure' in vals and vals['weight_configure']:
            res.update_weight()            
            weight_amount = res.weight
            if res.product_variant_ids:
                for product in res.product_variant_ids:
                    product.weight = weight_amount
        if 'weight' in vals and vals['weight']:
            res.update_weight_configure()

        if 'width_configure' in vals and vals['width_configure']:
            res.update_width()
        if 'width' in vals and vals['width']:
            res.update_width_configure()

        if 'height_configure' in vals and vals['height_configure']:
            res.update_height()
        if 'height' in vals and vals['height']:
            res.update_height_configure()

        if 'lenth' in vals and vals['lenth']:
            res.update_lenth_configure()
        if 'lenth_configure' in vals and vals['lenth_configure']:
            res.update_lenth()
        res._onchange_volume()
        return res

    def _compute_volume_uom(self):
        for obj in self:
            volume_uom = False
            cubic_feet = self.env.ref('uom.product_uom_cubic_foot')
            cubic_meter = self.env.ref('uom.product_uom_cubic_meter')
            uom_factor =  obj._get_volume_uom_id_from_ir_config_parameter()
            if cubic_feet and uom_factor and (cubic_feet.id == uom_factor.id):
                volume_uom = self.env.ref('uom.product_uom_foot').id
            if cubic_meter and uom_factor and (cubic_meter.id == uom_factor.id):
                volume_uom = self.env.ref('uom.product_uom_meter').id
            obj.volume_uom_id = volume_uom

    def update_weight(self):
        for obj in self:
            if obj.weight_configure:
                uom_factor = obj._get_weight_uom_id_from_ir_config_parameter()
                uom_kg = self.env.ref('uom.product_uom_kgm')                
                if uom_factor and uom_factor.factor == 'kg':
                    obj.with_context(updated_weight=1).weight = obj.weight_configure
                else:
                    obj.with_context(updated_weight=1).weight =  (uom_factor.factor * obj.weight_configure) / uom_kg.factor

    def update_weight_configure(self):
        for obj in self:
            if obj.weight:
                uom_factor = obj._get_weight_uom_id_from_ir_config_parameter()
                if uom_factor and uom_factor.factor == 'kg':
                    obj.weight = obj.weight_configure
                else:
                    try:
                        obj.with_context(update_weight_configure=1).weight_configure = obj.weight /  uom_factor.factor
                    except e:
                        pass

    def update_width(self):
        for obj in self:
            if obj.width_configure:
                uom_factor = obj.inch_uom_id
                cm_uom_id = self.env.ref('uom.product_uom_cm')
                if uom_factor and cm_uom_id:
                    try:
                        width = (obj.inch_uom_id.factor * obj.width_configure) / cm_uom_id.factor
                        obj.with_context(update_width=1).width = (obj.inch_uom_id.factor * obj.width_configure) / cm_uom_id.factor
                    except e:
                        pass

    def update_width_configure(self):
        for obj in self:
            if obj.width:
                uom_factor = obj.inch_uom_id
                cm_uom_id = self.env.ref('uom.product_uom_cm')
                if uom_factor and cm_uom_id:
                    try:
                        obj.with_context(update_width_configure=1).width_configure = (cm_uom_id.factor * obj.width) / uom_factor.factor
                    except e:
                        pass

    def update_height(self):
        for obj in self:
            if obj.height_configure:
                uom_factor = obj.inch_uom_id
                cm_uom_id = self.env.ref('uom.product_uom_cm')
                if uom_factor and cm_uom_id:
                    try:
                        obj.with_context(update_height=1).height = (obj.inch_uom_id.factor * obj.height_configure) / cm_uom_id.factor
                    except e:
                        pass


    def update_height_configure(self):
        for obj in self:
            if obj.height:
                uom_factor = obj.inch_uom_id
                cm_uom_id = self.env.ref('uom.product_uom_cm')
                if uom_factor and cm_uom_id:
                    try:
                        obj.with_context(update_height_configure=1).height_configure = (cm_uom_id.factor * obj.height) / uom_factor.factor
                    except e:
                        pass


    def update_lenth(self):
        for obj in self:
            if obj.lenth_configure:
                uom_factor = obj.inch_uom_id
                cm_uom_id = self.env.ref('uom.product_uom_cm')
                if uom_factor and cm_uom_id:
                    try:
                        obj.with_context(update_lenth=1).length = (obj.inch_uom_id.factor * obj.lenth_configure) / cm_uom_id.factor
                    except e:
                        pass

    def update_lenth_configure(self):
        for obj in self:
            if obj.length:
                uom_factor = obj.inch_uom_id
                cm_uom_id = self.env.ref('uom.product_uom_cm')
                if uom_factor and cm_uom_id:
                    try:
                        obj.with_context(update_lenth_configure=1).lenth_configure = (cm_uom_id.factor * obj.length) / uom_factor.factor
                    except e:
                        pass


    def write(self,vals):
        res = super(ProductTemplate,self).write(vals)
        if 'weight_configure' in vals and vals['weight_configure']:
            for obj in self:
                obj.update_weight()
        if 'updated_weight' in self.env.context:
            return res
        if 'weight' in vals and vals['weight']:
            for obj in self:
                obj.update_weight_configure()
        if 'update_weight_configure' in self.env.context:
            return res


        if 'width_configure' in vals and vals['width_configure']:
            for obj in self:
                obj.update_width()
        if 'update_width' in self.env.context:
            return res

        if 'width' in vals and vals['width']:
            for obj in self:
                obj.update_width_configure()
        if 'update_width_configure' in self.env.context:
            return res


        if 'height_configure' in vals and vals['height_configure']:
            for obj in self:
                obj.update_height()
        if 'update_height' in self.env.context:
            return res

        if 'height' in vals and vals['height']:
            for obj in self:
                obj.update_height_configure()
        if 'update_height_configure' in self.env.context:
            return res


        if 'lenth_configure' in vals and vals['lenth_configure']:
            for obj in self:
                obj.update_lenth()
        if 'update_lenth' in self.env.context:
            return res

        if 'lenth' in vals and vals['lenth']:
            for obj in self:
                obj.update_lenth_configure()
        if 'update_lenth_configure' in self.env.context:
            return res
        return res


    # @api.onchange('weight_configure')
    # def _onchange_weight_configure(self):
    #     for obj in self:
    #         if obj.weight_configure:
    #             uom_factor = obj._get_weight_uom_id_from_ir_config_parameter()
    #             uom_kg = self.env.ref('uom.product_uom_kgm')                
    #             if uom_factor and uom_factor.factor == 'kg':
    #                 obj.weight = obj.weight_configure
    #             else:
    #                 obj.weight =  (uom_factor.factor * obj.weight_configure) / uom_kg.factor


    # @api.onchange('weight')
    # def _onchange_weight(self):
    #     for obj in self:
    #         if obj.weight:
    #             uom_factor = obj._get_weight_uom_id_from_ir_config_parameter()
    #             if uom_factor and uom_factor.factor == 'kg':
    #                 obj.weight = obj.weight_configure
    #             else:
    #                 try:
    #                     obj.weight_configure = obj.weight /  uom_factor.factor
    #                 except e:
    #                     pass


    # @api.onchange('width_configure')
    # def _onchange_width_configure(self):
    #     for obj in self:
    #         if obj.width_configure:
    #             uom_factor = obj.inch_uom_id
    #             cm_uom_id = self.env.ref('uom.product_uom_cm')
    #             if uom_factor and cm_uom_id:
    #                 try:
    #                     width = (obj.inch_uom_id.factor * obj.width_configure) / cm_uom_id.factor
    #                     obj.width = (obj.inch_uom_id.factor * obj.width_configure) / cm_uom_id.factor
    #                 except e:
    #                     pass

    # @api.onchange('width')
    # def _onchange_width(self):
    #     for obj in self:
    #         if obj.width:
    #             uom_factor = obj.inch_uom_id
    #             cm_uom_id = self.env.ref('uom.product_uom_cm')
    #             if uom_factor and cm_uom_id:
    #                 try:
    #                     obj.width_configure = (cm_uom_id.factor * obj.width) / uom_factor.factor
    #                 except e:
    #                     pass


    # @api.onchange('lenth_configure')
    # def _onchange_lenth_configure(self):
    #     for obj in self:
    #         if obj.lenth_configure:
    #             uom_factor = obj.inch_uom_id
    #             cm_uom_id = self.env.ref('uom.product_uom_cm')
    #             if uom_factor and cm_uom_id:
    #                 try:
    #                     obj.length = (obj.inch_uom_id.factor * obj.lenth_configure) / cm_uom_id.factor
    #                 except e:
    #                     pass



    # @api.onchange('length')
    # def _onchange_length(self):
    #     for obj in self:
    #         if obj.length:
    #             uom_factor = obj.inch_uom_id
    #             cm_uom_id = self.env.ref('uom.product_uom_cm')
    #             if uom_factor and cm_uom_id:
    #                 try:
    #                     obj.lenth_configure = (cm_uom_id.factor * obj.length) / uom_factor.factor
    #                 except e:
    #                     pass

    # @api.onchange('height_configure')
    # def _onchange_height_configure(self):
    #     for obj in self:
    #         if obj.height_configure:
    #             uom_factor = obj.inch_uom_id
    #             cm_uom_id = self.env.ref('uom.product_uom_cm')
    #             if uom_factor and cm_uom_id:
    #                 try:
    #                     obj.height = (obj.inch_uom_id.factor * obj.height_configure) / cm_uom_id.factor
    #                 except e:
    #                     pass


    # @api.onchange('height')
    # def _onchange_height(self):
    #     for obj in self:
    #         if obj.height:
    #             uom_factor = obj.inch_uom_id
    #             cm_uom_id = self.env.ref('uom.product_uom_cm')
    #             if uom_factor and cm_uom_id:
    #                 try:
    #                     obj.height_configure = (cm_uom_id.factor * obj.height) / uom_factor.factor
    #                 except e:
    #                     pass


    @api.onchange('height','width','length','height_configure','width_configure','lenth_configure')
    def _onchange_volume(self):
        for obj in self:
            if obj.volume_uom_id and obj.volume_uom_id.name == 'm':
                metric_cubic = obj._get_volume_uom_id_from_ir_config_parameter().factor
                inch_cubic = self.env.ref('uom.product_uom_cubic_inch')
                volume_inch  = obj.height * obj.width * obj.length
                obj.volume = (volume_inch * metric_cubic) / inch_cubic.factor
            else:
                confi_metric_cube = obj._get_volume_uom_id_from_ir_config_parameter().factor
                cubic_inch = self.env.ref('uom.product_uom_cubic_inch')
                volume_inch  = obj.height * obj.width * obj.length
                obj.volume = (volume_inch * confi_metric_cube) / cubic_inch.factor


    def default_dim_uom(self):
        dimension_uom = self.env['uom.uom'].search([('name','=','m')],limit=1)
        return dimension_uom.name

    dimension_uom = fields.Char(string="Dim. UOM",default=default_dim_uom)   


    # @api.depends('product_variant_ids', 'product_variant_ids.height')
    # def _compute_height(self):
    #     unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
    #     for template in unique_variants:
    #         template.height = template.product_variant_ids.height
    #     for template in (self - unique_variants):
    #         template.height = 0.0

    # @api.depends('product_variant_ids', 'product_variant_ids.length')
    # def _compute_length(self):
    #     unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
    #     for template in unique_variants:
    #         template.length = template.product_variant_ids.length
    #     for template in (self - unique_variants):
    #         template.length = 0.0

    # @api.depends('product_variant_ids', 'product_variant_ids.width')
    # def _compute_width(self):
    #     unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
    #     for template in unique_variants:
    #         template.width = template.product_variant_ids.width
    #     for template in (self - unique_variants):
    #         template.width = 0.0

    # def _set_width(self):
    #     for template in self:
    #         if len(template.product_variant_ids) == 1:
    #             template.product_variant_ids.width = template.width

    # def _set_length(self):
    #     for template in self:
    #         if len(template.product_variant_ids) == 1:
    #             template.product_variant_ids.length = template.length

    # def _set_height(self):
    #     for template in self:
    #         if len(template.product_variant_ids) == 1:
    #             template.product_variant_ids.height = template.height    


    # @api.model_create_multi
    # def create(self, vals_list):
    #     templates = super(ProductTemplate, self).create(vals_list)
    #     for template, vals in zip(templates, vals_list):
    #         related_vals = {}
    #         if vals.get('height'):
    #             related_vals['height'] = vals['height']
    #         if vals.get('length'):
    #             related_vals['length'] = vals['length']
    #         if vals.get('width'):
    #             related_vals['width'] = vals['width']
    #         if related_vals:
    #             template.write(related_vals)
    #     return templates