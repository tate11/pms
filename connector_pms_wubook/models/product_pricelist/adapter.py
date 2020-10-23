# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _

from odoo.addons.component.core import Component
from odoo.addons.connector_pms.components.adapter import ChannelAdapterError


class ChannelWubookProductPricelistAdapter(Component):
    _name = "channel.wubook.product.pricelist.adapter"
    _inherit = "channel.wubook.adapter"

    _apply_on = "channel.wubook.product.pricelist"

    # CRUD
    # pylint: disable=W8106
    def create(self, values):
        # https://tdocs.wubook.net/wired/rooms.html#new_room
        params = self._prepare_parameters(
            values,
            ["woodoo", "name", "beds", "defprice", "avail", "shortname", "defboard"],
            [
                "names",
                "descriptions",
                "boards",
                "rtype",
                ("min_price", 0),
                ("max_price", 0),
            ],
        )
        _id = self._exec("new_room", *params)
        return _id

    def read(self, _id):
        # https://tdocs.wubook.net/wired/rooms.html#fetch_single_room
        values = self._exec("fetch_single_room", _id)
        if not values:
            raise ChannelAdapterError(_("No data received"))
        if len(values) != 1:
            raise ChannelAdapterError(_("Received more than one room %s") % (values,))
        return values[0]

    def search_read(self, domain, ancillary=0):
        # https://tdocs.wubook.net/wired/rooms.html#fetch_rooms
        values = self._exec("fetch_rooms", ancillary)
        return self._filter(values, domain)

    def search(self, domain, ancillary=0):
        # https://tdocs.wubook.net/wired/rooms.html#fetch_rooms
        values = self.search_read(domain, ancillary=ancillary)
        ids = [x[self._id] for x in values]
        return ids

    # pylint: disable=W8106
    def write(self, _id, values):
        # https://tdocs.wubook.net/wired/rooms.html#mod_room
        params = self._prepare_parameters(
            values,
            ["name", "beds", "defprice", "avail", "shortname", "defboard"],
            [
                "names",
                "descriptions",
                "boards",
                ("min_price", 0),
                ("max_price", 0),
                "rtype",
                "woodoo_only",
            ],
        )
        _id = self._exec("mod_room", _id, *params)
        return _id

    def delete(self, _id):
        # https://tdocs.wubook.net/wired/rooms.html#del_room
        res = self._exec("del_room", _id)
        return res

    # MISC
    def images(self, _id):
        # https://tdocs.wubook.net/wired/rooms.html#room_images
        values = self._exec("room_images", _id)
        return values

    def push_update_activation(self, url):
        # https://tdocs.wubook.net/wired/rooms.html#push_update_activation
        self._exec("push_update_activation", url)

    def push_update_url(self):
        # https://tdocs.wubook.net/wired/rooms.html#push_update_url
        url = self._exec("push_update_url")
        return url
