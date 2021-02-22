# Copyright 2019-2021 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class InheritResCompany(models.Model):
    _inherit = "pms.property"

    # data_bi_id = fields.Integer(
    #     "Unique ID for DataBI",
    #     default=0,
    #     help="It must be unique to be able to identify the hotel, \
    #     within a hotel group.",
    # )
    expedia_rate = fields.Integer(
        "Expedia Rate DataBI",
        default=18,
        required=True,
        digits=(2),
        help="It is the commission percentage negotiated with the \
        Expedia company, expressed with two digits. \
        Example: 18 = 18% commission.",
    )
    data_bi_days = fields.Integer(
        "Days to download",
        default=60,
        required=True,
        digits=(3),
        help="Number of days, which are downloaded data, \
        backwards, by default are 60 days to download.",
    )
