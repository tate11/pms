# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class PmsRoomTypeAvailability(models.Model):
    """The room type availability is used as a daily availability plan for room types
    and therefore is related only with one property."""

    _name = "pms.room.type.availability.plan"
    _description = "Reservation availability plan"

    # Default methods
    @api.model
    def _get_default_pms_property(self):
        return self.env.user.get_active_property_ids()[0] or None

    # Fields declaration
    name = fields.Char("Availability Plan Name", required=True)
    pms_property_ids = fields.Many2many(
        comodel_name="pms.property",
        string="Properties",
        ondelete="restrict",
    )

    pms_pricelist_ids = fields.One2many(
        comodel_name="product.pricelist",
        inverse_name="availability_plan_id",
        string="Pricelists",
        required=False,
    )

    rule_ids = fields.One2many(
        comodel_name="pms.room.type.availability.rule",
        inverse_name="availability_plan_id",
        string="Availability Rules",
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="If unchecked, it will allow you to hide the "
        "Availability plan without removing it.",
    )

    # Business Methods
    @classmethod
    def any_rule_applies(cls, checkin, checkout, item):
        reservation_len = (checkout - checkin).days
        return any(
            [
                (0 < item.max_stay < reservation_len),
                (0 < item.min_stay > reservation_len),
                (0 < item.max_stay_arrival < reservation_len and checkin == item.date),
                (0 < item.min_stay_arrival > reservation_len and checkin == item.date),
                item.closed,
                (item.closed_arrival and checkin == item.date),
                (item.closed_departure and checkout == item.date),
                (item.quota == 0 or item.max_avail == 0),
            ]
        )

    @api.model
    def rooms_available(
        self,
        checkin,
        checkout,
        room_type_id=False,
        current_lines=False,
        pricelist_id=False,
        pms_property_id=False,
    ):
        if current_lines and not isinstance(current_lines, list):
            current_lines = [current_lines]
        free_rooms = self.get_real_free_rooms(
            checkin, checkout, room_type_id, current_lines, pms_property_id
        )
        domain_rules = [
            ("date", ">=", checkin),
            (
                "date",
                "<=",
                checkout,
            ),  # TODO: only closed_departure take account checkout date!
        ]
        if pms_property_id:
            domain_rules.append(("pms_property_id", "=", pms_property_id))

        if room_type_id:
            domain_rules.append(("room_type_id", "=", room_type_id))
        if pricelist_id:
            pricelist = self.env["product.pricelist"].browse(pricelist_id)
            if pricelist and pricelist.availability_plan_id:
                domain_rules.append(
                    ("availability_plan_id", "=", pricelist.availability_plan_id.id)
                )
                rule_items = self.env["pms.room.type.availability.rule"].search(
                    domain_rules
                )

                if len(rule_items) > 0:
                    room_types_to_remove = []
                    for item in rule_items:
                        if self.any_rule_applies(checkin, checkout, item):
                            room_types_to_remove.append(item.room_type_id.id)
                    free_rooms = free_rooms.filtered(
                        lambda x: x.room_type_id.id not in room_types_to_remove
                    )
            elif not pricelist:
                raise ValidationError(_("Pricelist not found"))
        return free_rooms.sorted(key=lambda r: r.sequence)

    def get_real_free_rooms(
        self,
        checkin,
        checkout,
        room_type_id=False,
        current_lines=False,
        pms_property_id=False,
    ):
        Avail = self.env["pms.room.type.availability"]
        if isinstance(checkin, str):
            checkin = datetime.datetime.strptime(
                checkin, DEFAULT_SERVER_DATE_FORMAT
            ).date()
        if isinstance(checkout, str):
            checkout = datetime.datetime.strptime(
                checkout, DEFAULT_SERVER_DATE_FORMAT
            ).date()
        domain = [
            ("date", ">=", checkin),
            ("date", "<=", checkout - datetime.timedelta(1)),
        ]
        if not current_lines:
            current_lines = []
        rooms_not_avail = (
            Avail.search(domain)
            .reservation_line_ids.filtered(lambda l: l.id and l.id not in current_lines)
            .room_id.ids
        )
        domain_rooms = []
        if rooms_not_avail:
            domain_rooms = [
                ("id", "not in", rooms_not_avail),
            ]
        if pms_property_id:
            domain_rooms.append(("pms_property_id", "=", pms_property_id))
        if room_type_id:
            domain_rooms.append(("room_type_id", "=", room_type_id))
        return self.env["pms.room"].search(domain_rooms)

    @api.model
    def get_count_rooms_available(
        self,
        checkin,
        checkout,
        room_type_id,
        pms_property_id,
        current_lines=False,
        pricelist_id=False,
    ):
        if current_lines and not isinstance(current_lines, list):
            current_lines = [current_lines]

        avail = self.get_count_real_free_rooms(
            checkin, checkout, room_type_id, pms_property_id, current_lines
        )
        domain_rules = [
            ("date", ">=", checkin),
            (
                "date",
                "<=",
                checkout,
            ),  # TODO: only closed_departure take account checkout date!
            ("room_type_id", "=", room_type_id),
            ("pms_property_id", "=", pms_property_id),
        ]
        if pricelist_id:
            pricelist = self.env["product.pricelist"].browse(pricelist_id)
        if pricelist and pricelist.availability_plan_id:
            domain_rules.append(
                ("availability_plan_id", "=", pricelist.availability_plan_id.id)
            )
            rule_items = self.env["pms.room.type.availability.rule"].search(
                domain_rules
            )
            if len(rule_items) > 0:
                for item in rule_items:
                    if self.any_rule_applies(checkin, checkout, item):
                        return 0
                avail = min(rule_items.mapped("plan_avail"))
        return avail

    def get_count_real_free_rooms(
        self,
        checkin,
        checkout,
        room_type_id,
        pms_property_id,
        current_lines=False,
    ):
        Avail = self.env["pms.room.type.availability"]
        count_free_rooms = len(self.env["pms.room.type"].browse(room_type_id).room_ids)
        if isinstance(checkin, str):
            checkin = datetime.datetime.strptime(
                checkin, DEFAULT_SERVER_DATE_FORMAT
            ).date()
        if isinstance(checkout, str):
            checkout = datetime.datetime.strptime(
                checkout, DEFAULT_SERVER_DATE_FORMAT
            ).date()
        for avail in Avail.search(
            [
                ("date", ">=", checkin),
                ("date", "<=", checkout - datetime.timedelta(1)),
                ("room_type_id", "=", room_type_id),
                ("pms_property_id", "=", pms_property_id),
            ]
        ):
            if avail.real_avail < count_free_rooms:
                count_free_rooms = avail.real_avail
        return count_free_rooms

    @api.model
    def splitted_availability(
        self,
        checkin,
        checkout,
        room_type_id=False,
        current_lines=False,
        pricelist=False,
        pms_property_id=False,
    ):
        if isinstance(checkin, str):
            checkin = datetime.datetime.strptime(
                checkin, DEFAULT_SERVER_DATE_FORMAT
            ).date()
        if isinstance(checkout, str):
            checkout = datetime.datetime.strptime(
                checkout, DEFAULT_SERVER_DATE_FORMAT
            ).date()
        for date_iterator in [
            checkin + datetime.timedelta(days=x)
            for x in range(0, (checkout - checkin).days)
        ]:
            rooms_avail = self.rooms_available(
                checkin=date_iterator,
                checkout=date_iterator + datetime.timedelta(1),
                room_type_id=room_type_id,
                current_lines=current_lines,
                pricelist_id=pricelist.id,
                pms_property_id=pms_property_id,
            )
            if len(rooms_avail) < 1:
                return False
        return True

    @api.model
    def update_quota(self, pricelist_id, room_type_id, date, line):
        if pricelist_id and room_type_id and date:
            rule = self.env["pms.room.type.availability.rule"].search(
                [
                    ("availability_plan_id.pms_pricelist_ids", "=", pricelist_id.id),
                    ("room_type_id", "=", room_type_id.id),
                    ("date", "=", date),
                ]
            )
            # applies a rule
            if rule:
                rule.ensure_one()
                if rule and rule.quota != -1 and rule.quota > 0:

                    # the line has no rule item applied before
                    if not line.impacts_quota:
                        rule.quota -= 1
                        return rule.id

                    # the line has a rule item applied before
                    elif line.impacts_quota != rule.id:

                        # decrement quota on current rule item
                        rule.quota -= 1

                        # check old rule item
                        old_rule = self.env["pms.room.type.availability.rule"].search(
                            [("id", "=", line.impacts_quota)]
                        )

                        # restore quota in old rule item
                        if old_rule:
                            old_rule.quota += 1

                        return rule.id

        # in any case, check old rule item
        if line.impacts_quota:
            old_rule = self.env["pms.room.type.availability.rule"].search(
                [("id", "=", line.impacts_quota)]
            )
            # and restore quota in old rule item
            if old_rule:
                old_rule.quota += 1

        return False

    # Action methods
    def open_massive_changes_wizard(self):

        if self.ensure_one():
            return {
                "view_type": "form",
                "view_mode": "form",
                "name": "Massive changes on Availability Plan: " + self.name,
                "res_model": "pms.massive.changes.wizard",
                "target": "new",
                "type": "ir.actions.act_window",
                "context": {
                    "availability_plan_id": self.id,
                },
            }
