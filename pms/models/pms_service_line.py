# Copyright 2017-2018  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsServiceLine(models.Model):
    _name = "pms.service.line"
    _description = "Service by day"
    _order = "date"

    # Fields declaration
    service_id = fields.Many2one(
        "pms.service",
        string="Service Room",
        ondelete="cascade",
        required=True,
        copy=False,
    )
    product_id = fields.Many2one(related="service_id.product_id", store=True)
    tax_ids = fields.Many2many(
        "account.tax", string="Taxes", related="service_id.tax_ids", readonly="True"
    )
    pms_property_id = fields.Many2one(
        "pms.property", store=True, readonly=True, related="service_id.pms_property_id"
    )
    date = fields.Date("Date")
    day_qty = fields.Integer("Units")
    price_unit = fields.Float(
        "Unit Price",
        digits=("Product Price"),
    )
    room_id = fields.Many2one(
        string="Room", related="service_id.reservation_id", readonly=True, store=True
    )
    discount = fields.Float(
        "Discount", related="service_id.discount", readonly=True, store=True
    )
    cancel_discount = fields.Float(
        "Cancelation Discount", compute="_compute_cancel_discount"
    )

    # Depends
    # TODO: Refact method and allowed cancelled single days
    @api.depends("service_id.reservation_id.cancelled_reason")
    def _compute_cancel_discount(self):
        for line in self:
            line.cancel_discount = 0
            # TODO: Review cancel logic
            # reservation = line.reservation_id.reservation_id
            # pricelist = reservation.pricelist_id
            # if reservation.state == "cancelled":
            #     if (
            #         reservation.cancelled_reason
            #         and pricelist
            #         and pricelist.cancelation_rule_id
            #     ):
            #         date_start_dt = fields.Date.from_string(
            #             reservation.checkin
            #         )
            #         date_end_dt = fields.Date.from_string(
            #             reservation.checkout
            #         )
            #         days = abs((date_end_dt - date_start_dt).days)
            #         rule = pricelist.cancelation_rule_id
            #         if reservation.cancelled_reason == "late":
            #             discount = 100 - rule.penalty_late
            #             if rule.apply_on_late == "first":
            #                 days = 1
            #             elif rule.apply_on_late == "days":
            #                 days = rule.days_late
            #         elif reservation.cancelled_reason == "noshow":
            #             discount = 100 - rule.penalty_noshow
            #             if rule.apply_on_noshow == "first":
            #                 days = 1
            #             elif rule.apply_on_noshow == "days":
            #                 days = rule.days_late - 1
            #         elif reservation.cancelled_reason == "intime":
            #             discount = 100

            #         checkin = reservation.checkin
            #         dates = []
            #         for i in range(0, days):
            #             dates.append(
            #                 (
            #                     fields.Date.from_string(checkin) + timedelta(days=i)
            #                 ).strftime(DEFAULT_SERVER_DATE_FORMAT)
            #             )
            #         reservation.reservation_line_ids.filtered(
            #             lambda r: r.date in dates
            #         ).update({"cancel_discount": discount})
            #         reservation.reservation_line_ids.filtered(
            #             lambda r: r.date not in dates
            #         ).update({"cancel_discount": 100})
            #     else:
            #         reservation.reservation_line_ids.update({"cancel_discount": 0})
            # else:
            #     reservation.reservation_line_ids.update({"cancel_discount": 0})

    # Constraints and onchanges
    @api.constrains("day_qty")
    def no_free_resources(self):
        for record in self:
            limit = record.product_id.daily_limit
            if limit > 0:
                out_qty = sum(
                    self.env["pms.service.line"]
                    .search(
                        [
                            ("product_id", "=", record.product_id.id),
                            ("date", "=", record.date),
                            ("service_id", "!=", record.service_id.id),
                        ]
                    )
                    .mapped("day_qty")
                )
                if limit < out_qty + record.day_qty:
                    raise ValidationError(
                        _("%s limit exceeded for %s")
                        % (record.service_id.product_id.name, record.date)
                    )

    # Business methods
    def _cancel_discount(self):
        for record in self:
            if record.reservation_id:
                day = record.reservation_id.reservation_line_ids.filtered(
                    lambda d: d.date == record.date
                )
                record.cancel_discount = day.cancel_discount
