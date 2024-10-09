from odoo import api, fields, models



class ContractLines(models.Model):
    _name = 'contract.lines'
    _description = 'Contract Lines'

    name = fields.Char()
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='',
        required=False)
    contract_start_date = fields.Date(
        string='Contract Start Date',
        required=False)
    contract_end_date = fields.Date(
        string='Contract End Date',
        required=False)
    qty = fields.Float(
        string='Quantity',
        required=False)
    price = fields.Float(
        string='unit Price',
        required=False)
    withdrawn_quantity = fields.Float(
        string='Withdrawn Quantity',compute='_compute_ordered_qty_po'

    )

    remaining_quantity = fields.Float(
        string='Remaining Quantity',
        compute='_get_remaining_quantity',
        readonly=True,
        required=False)
    quantity_sent = fields.Float(
        string='Quantity Sent',compute='_compute_vehicles_qty_sent')
    contract_ids = fields.Many2one(
        comodel_name='contract.contract',
        string='Contract Ids',
        required=False)
    load_place = fields.Many2one(
        comodel_name='place.place',
        string='Load Place',
        required=False)
    unloading_place = fields.Many2one(
        comodel_name='place.place',
        string='Unloading Location',
        required=False)
    contract_type = fields.Selection(related='contract_ids.contract_type' ,)

    contract  = fields.Boolean(
        string='', 
        required=False)
    lots_id = fields.Many2many(
        comodel_name='stock.lot',
        string='')

    lot_id = fields.Many2one(
        'stock.lot',
        string='Operation',domain="[('id', 'in', lots_id)]"
    )
    total_price  = fields.Float(
        string='cost',compute='_compute_total_price',store=True,
        required=False)
    assigning_party  = fields.Many2one(
        comodel_name='assign.assign',
        string='assigning',
        required=False)



    @api.depends('qty', 'price')
    def _compute_total_price(self):
        for rec in self:
            if rec.qty or rec.price:
                rec.total_price = rec.price * rec.qty





    def _get_remaining_quantity(self):
        for rec in self:
            if rec.remaining_quantity or rec.qty:
                rec.remaining_quantity = rec.qty - rec.withdrawn_quantity




    def _compute_ordered_qty_po(self):
        for line in self:
            if line.contract_ids.contract_type == 'indirect':
                total = 0.0
                if line.contract_ids:
                    for po in line.contract_ids.purchase_ids.filtered(
                            lambda po: po.state in ['purchase', 'done']):
                        for po_line in po.order_line.filtered(
                                lambda po_line: po_line.product_id == line.product_id and po_line.lot_id == line.lot_id):
                            total += po_line.product_qty
                    line.withdrawn_quantity = total
                else:
                    line.withdrawn_quantity = 0
            elif line.contract_ids.contract_type == 'transfer':
                total_withdrawn_quantity = 0.0
                contracts = line.contract_ids.orders
                for contract in contracts:
                    if contract.partner_id == line.contract_ids.customer:
                        for product in contract.order_line:
                            if product.product_id == line.product_id:
                                total_withdrawn_quantity += product.product_uom_qty
                line.withdrawn_quantity = total_withdrawn_quantity
            else:
                total_withdrawn_quantity = 0.0
                vehicles = line.contract_ids.vehicles
                if vehicles:
                    for vehicle in vehicles:
                        if vehicle.partner_id == line.contract_ids.customer and vehicle.service_id == line.product_id:
                            qty = vehicle.loaded_qty
                            total_withdrawn_quantity += qty
                line.withdrawn_quantity = total_withdrawn_quantity

    def _compute_vehicles_qty_sent(self):
        for line in self:
            total_sent_quantity = 0.0  # Reset for each line
            vehicles = line.contract_ids.vehicles
            if vehicles:
                for vehicle in vehicles:
                    if vehicle.partner_id == line.contract_ids.customer and vehicle.service_id == line.product_id:
                        total_sent_quantity += vehicle.loaded_qty
            line.quantity_sent = total_sent_quantity



    @api.depends('purchase_ids')
    def _compute_orders_number(self):
        for requisition in self:
            requisition.order_count = len(requisition.purchase_ids)



    @api.onchange('product_id')
    def _get_lots_for_products(self):
        po = None
        lots = []
        if self.product_id:
            products_ids = self.env['stock.lot'].sudo().search([('product_id', '=', self.product_id.id)])
            print("@@@@@@@@@@@@@@@@@@@", products_ids)
            for lot in products_ids:
                print("lots is", lot.id)
                po = lot.id
                lots.append(lot.id)
                self.lots_id = lots
            print("po", po)
        if po:
            return {'domain': {'lot_id': [('id', 'in', lots)]}}
        else:
            return {'domain': {'lot_id': [('id', '=', False)]}}
















