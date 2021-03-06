import datetime

from odoo import api, fields, models


class AvailabilityWizard(models.TransientModel):

    _name = "pms.massive.changes.wizard"
    _description = "Wizard for massive changes on Availability Plans & Pricelists."

    def _default_avail_readonly(self):
        return True if self._context.get("availability_plan_id") else False

    def _default_pricelist_readonly(self):
        return True if self._context.get("pricelist_id") else False

    # Fields declaration
    pms_property_ids = fields.Many2many(
        comodel_name="pms.property",
        string="Property",
        default=lambda self: self.env["pms.property"].browse(
            self.env.user.get_active_property_ids()[0]
        ),
    )
    massive_changes_on = fields.Selection(
        [("pricelist", "Pricelist"), ("availability_plan", "Availability Plan")],
        string="Massive changes on",
        default="availability_plan",
        required=True,
    )
    availability_plan_id = fields.Many2one(
        comodel_name="pms.room.type.availability.plan",
        string="Availability Plan to apply massive changes",
        # can be setted by context from availability plan detail
    )
    pricelist_id = fields.Many2one(
        comodel_name="product.pricelist",
        string="Pricelist to apply massive changes",
    )
    allowed_pricelist_ids = fields.One2many(
        comodel_name="product.pricelist", compute="_compute_allowed_pricelist_ids"
    )
    start_date = fields.Date(
        string="From:",
        required=True,
    )
    end_date = fields.Date(
        string="To:",
        required=True,
    )
    room_type_id = fields.Many2one(comodel_name="pms.room.type", string="Room Type")
    price = fields.Float(string="Price")
    min_quantity = fields.Float(string="Min. Quantity")

    min_stay = fields.Integer(
        string="Min. Stay",
        default=0,
    )
    min_stay_arrival = fields.Integer(
        string="Min. Stay Arrival",
        default=0,
    )
    max_stay = fields.Integer(
        string="Max. Stay",
        default=0,
    )
    max_stay_arrival = fields.Integer(
        string="Max. Stay Arrival",
        default=0,
    )
    closed = fields.Boolean(
        string="Closed",
        default=False,
    )
    closed_departure = fields.Boolean(
        string="Closed Departure",
        default=False,
    )
    closed_arrival = fields.Boolean(
        string="Closed Arrival",
        default=False,
    )
    quota = fields.Integer(
        string="Quota",
        help="Generic Quota assigned.",
        default=-1,
    )
    max_avail = fields.Integer(
        string="Max. Availability",
        help="Maximum simultaneous availability on own Booking Engine.",
        default=-1,
    )
    apply_on_monday = fields.Boolean(
        string="Apply Availability Rule on mondays",
        default=False,
    )
    apply_on_tuesday = fields.Boolean(
        string="Apply Availability Rule on tuesdays",
        default=False,
    )
    apply_on_wednesday = fields.Boolean(
        string="Apply Availability Rule on wednesdays",
        default=False,
    )
    apply_on_thursday = fields.Boolean(
        string="Apply Availability Rule on thursdays",
        default=False,
    )
    apply_on_friday = fields.Boolean(
        string="Apply Availability Rule on fridays",
        default=False,
    )
    apply_on_saturday = fields.Boolean(
        string="Apply Availability Rule on saturdays",
        default=False,
    )
    apply_on_sunday = fields.Boolean(
        string="Apply Availability Rule on sundays",
        default=False,
    )
    apply_on_all_week = fields.Boolean(
        string="Apply Availability Rule for the whole week",
        default=True,
    )
    rules_to_overwrite = fields.One2many(
        comodel_name="pms.room.type.availability.rule",
        compute="_compute_rules_to_overwrite",
        store=False,
        readonly=True,
    )
    pricelist_items_to_overwrite = fields.One2many(
        comodel_name="product.pricelist.item",
        compute="_compute_pricelist_items_to_overwrite",
        store=False,
        readonly=True,
    )
    num_rules_to_overwrite = fields.Integer(
        string="Rules to overwrite on massive changes",
        compute="_compute_num_rules_to_overwrite",
        store=False,
        readonly=True,
    )
    num_pricelist_items_to_overwrite = fields.Integer(
        string="Pricelist items to overwrite on massive changes",
        compute="_compute_num_pricelist_items_to_overwrite",
        store=False,
        readonly=True,
    )
    avail_readonly = fields.Boolean(default=_default_avail_readonly)
    pricelist_readonly = fields.Boolean(default=_default_pricelist_readonly)

    @api.depends("massive_changes_on")
    def _compute_allowed_pricelist_ids(self):
        for record in self:
            record.allowed_pricelist_ids = self.env["product.pricelist"].search(
                [
                    ("pricelist_type", "=", "daily"),
                ]
            )

    @api.depends(
        "start_date",
        "end_date",
        "room_type_id",
        "apply_on_monday",
        "apply_on_tuesday",
        "apply_on_wednesday",
        "apply_on_thursday",
        "apply_on_friday",
        "apply_on_saturday",
        "apply_on_sunday",
        "apply_on_all_week",
        "availability_plan_id",
    )
    def _compute_rules_to_overwrite(self):
        for record in self:

            if not record.availability_plan_id and self._context.get(
                "availability_plan_id"
            ):
                record.availability_plan_id = self._context.get("availability_plan_id")
                record.massive_changes_on = "availability_plan"

            if record.availability_plan_id:
                domain = [
                    ("availability_plan_id", "=", record.availability_plan_id.id),
                ]

                if record.room_type_id:
                    domain.append(("room_type_id", "=", record.room_type_id.id))
                if record.start_date:
                    domain.append(("date", ">=", record.start_date))
                if record.end_date:
                    domain.append(("date", "<=", record.end_date))

                week_days_to_apply = (
                    record.apply_on_monday,
                    record.apply_on_tuesday,
                    record.apply_on_wednesday,
                    record.apply_on_thursday,
                    record.apply_on_friday,
                    record.apply_on_saturday,
                    record.apply_on_sunday,
                )
                if record.start_date and record.end_date:
                    rules = self.env["pms.room.type.availability.rule"].search(domain)
                    if (
                        not record.apply_on_all_week
                        and record.start_date
                        and record.end_date
                    ):
                        record.rules_to_overwrite = rules.filtered(
                            lambda x: week_days_to_apply[x.date.timetuple()[6]]
                        )
                    else:
                        record.rules_to_overwrite = rules
                else:
                    record.rules_to_overwrite = False
            else:
                record.rules_to_overwrite = False

    @api.depends(
        "start_date",
        "end_date",
        "room_type_id",
        "apply_on_monday",
        "apply_on_tuesday",
        "apply_on_wednesday",
        "apply_on_thursday",
        "apply_on_friday",
        "apply_on_saturday",
        "apply_on_sunday",
        "apply_on_all_week",
        "pricelist_id",
    )
    def _compute_pricelist_items_to_overwrite(self):
        for record in self:

            if not record.pricelist_id and self._context.get("pricelist_id"):
                record.pricelist_id = self._context.get("pricelist_id")
                record.massive_changes_on = "pricelist"

            if record.pricelist_id:
                domain = [
                    ("pricelist_id", "=", record.pricelist_id.id),
                    "|",
                    ("pms_property_ids", "=", False),
                    ("pms_property_ids", "in", record.pms_property_ids.ids),
                ]

                if record.start_date:
                    domain.append(("date_start_overnight", ">=", record.start_date))
                if record.end_date:
                    domain.append(("date_end_overnight", "<=", record.end_date))

                if record.room_type_id:
                    domain.append(
                        (
                            "product_tmpl_id",
                            "=",
                            record.room_type_id.product_id.product_tmpl_id.id,
                        )
                    )

                week_days_to_apply = (
                    record.apply_on_monday,
                    record.apply_on_tuesday,
                    record.apply_on_wednesday,
                    record.apply_on_thursday,
                    record.apply_on_friday,
                    record.apply_on_saturday,
                    record.apply_on_sunday,
                )

                if record.start_date and record.end_date:
                    items = self.env["product.pricelist.item"].search(domain)
                    if (
                        not record.apply_on_all_week
                        and record.start_date
                        and record.end_date
                    ):
                        record.pricelist_items_to_overwrite = items.filtered(
                            lambda x: week_days_to_apply[
                                x.date_end_overnight.timetuple()[6]
                            ]
                        )
                    else:
                        record.pricelist_items_to_overwrite = items
                else:
                    record.pricelist_items_to_overwrite = False
            else:
                record.pricelist_items_to_overwrite = False

    @api.depends(
        "rules_to_overwrite",
    )
    def _compute_num_rules_to_overwrite(self):
        for record in self:
            self.num_rules_to_overwrite = len(record.rules_to_overwrite)

    @api.depends(
        "pricelist_items_to_overwrite",
    )
    def _compute_num_pricelist_items_to_overwrite(self):
        for record in self:
            self.num_pricelist_items_to_overwrite = len(
                record.pricelist_items_to_overwrite
            )

    # actions
    def apply_massive_changes(self):

        for record in self:
            # remove old rules
            record.rules_to_overwrite.unlink()
            record.pricelist_items_to_overwrite.unlink()
            week_days_to_apply = (
                record.apply_on_monday,
                record.apply_on_tuesday,
                record.apply_on_wednesday,
                record.apply_on_thursday,
                record.apply_on_friday,
                record.apply_on_saturday,
                record.apply_on_sunday,
            )

            # dates between start and end (both included)
            for date in [
                record.start_date + datetime.timedelta(days=x)
                for x in range(0, (record.end_date - record.start_date).days + 1)
            ]:

                if (
                    not record.apply_on_all_week
                    and not week_days_to_apply[date.timetuple()[6]]
                ):
                    continue

                if not record.room_type_id:
                    room_types = self.env["pms.room.type"].search(
                        [
                            "|",
                            ("pms_property_ids", "=", False),
                            ("pms_property_ids", "in", record.pms_property_ids.ids),
                        ]
                    )
                else:
                    room_types = [record.room_type_id]
                for room_type in room_types:
                    for pms_property in record.pms_property_ids:
                        if record.massive_changes_on == "pricelist":
                            self.env["product.pricelist.item"].create(
                                {
                                    "pricelist_id": record.pricelist_id.id,
                                    "date_start_overnight": date,
                                    "date_end_overnight": date,
                                    "compute_price": "fixed",
                                    "applied_on": "0_product_variant",
                                    "product_id": room_type.product_id.id,
                                    "fixed_price": record.price,
                                    "min_quantity": record.min_quantity,
                                    "pms_property_ids": [pms_property.id],
                                }
                            )
                        else:
                            avail_plan_id = record.availability_plan_id.id
                            self.env["pms.room.type.availability.rule"].create(
                                {
                                    "availability_plan_id": avail_plan_id,
                                    "date": date,
                                    "room_type_id": room_type.id,
                                    "quota": record.quota,
                                    "max_avail": record.max_avail,
                                    "min_stay": record.min_stay,
                                    "min_stay_arrival": record.min_stay_arrival,
                                    "max_stay": record.max_stay,
                                    "max_stay_arrival": record.max_stay_arrival,
                                    "closed": record.closed,
                                    "closed_arrival": record.closed_arrival,
                                    "closed_departure": record.closed_departure,
                                    "pms_property_id": pms_property.id,
                                }
                            )
            if (
                record.massive_changes_on == "pricelist"
                and not record.pricelist_readonly
            ):
                action = self.env.ref("product.product_pricelist_action2").read()[0]
                action["views"] = [
                    (self.env.ref("pms.product_pricelist_view_form").id, "form")
                ]
                action["res_id"] = record.pricelist_id.id
                return action
            if (
                record.massive_changes_on == "availability_plan"
                and not record.avail_readonly
            ):
                action = self.env.ref("pms.room_type_availability_action").read()[0]
                action["views"] = [
                    (self.env.ref("pms.room_type_availability_view_form").id, "form")
                ]
                action["res_id"] = record.availability_plan_id.id
                return action
