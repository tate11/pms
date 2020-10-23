# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import mock

from odoo.addons.component.tests.common import SavepointComponentCase

_logger = logging.getLogger(__name__)


class WubookMockServer:
    _id = "id"
    _meta_fields = {"token", "lcode"}
    _unique_keys = {
        "pk": [_id],
        "uk1": ["shortname"],
    }

    def __init__(self):
        self.data = {}

        self.all_fields = {
            "name": "Test room type r9",
            "rtype": 9,
            "rtype_name": "Room type 9",
            "price": 33.0,
            "men": 5,
            "subroom": 0,
            "occupancy": 5,
            "id": 9,
            "board": "ai",
            "availability": 5,
            "shortname": "c9",
            "min_price": 0,
            "max_price": 0,
            "children": 0,
            "boards": "",
            "anchorate": 0,
            "dec_avail": 0,
            "woodoo": 0,
        }

    # main methods
    def fetch_rooms_mock(self, token, lcode, **kwargs):
        if lcode not in self.data:
            return -1, "The property '%s' does not exist" % lcode
        return 0, list(self.data[lcode].values())

    def fetch_single_room_mock(self, token, lcode, rcode, **kwargs):
        if lcode not in self.data:
            return -1, "The property '%s' does not exist" % lcode
        if rcode not in self.data[lcode]:
            return -2, "The room type '{}' does not exist on property '{}'".format(
                rcode,
                lcode,
            )
        return 0, [self.data[lcode][rcode]]

    def new_room_mock(self, *args):
        fields = [
            "token",
            "lcode",
            "woodoo",
            "name",
            "occupancy",
            "price",
            "availability",
            "shortname",
            "board",
            "names",
            "descriptions",
            "boards",
            "rtype",
            "min_price",
            "max_price",
        ]
        data = dict(list(zip(fields, args)))
        lcode = data["lcode"]
        data.update({k: False for k in set(self.all_fields.keys()) - set(fields)})
        for k in self._meta_fields:
            del data[k]
        self.data.setdefault(lcode, {})
        rid = self.data[lcode] and max(self.data[lcode].keys()) + 1 or 1
        data[self._id] = rid
        res, info = self._check_unique_keys(lcode, data)
        if res:
            return res, info
        self.data[lcode][rid] = data
        return 0, rid

    def mod_room_mock(self, *args, **kwargs):
        fields = [
            "token",
            "lcode",
            "id",
            "name",
            "occupancy",
            "price",
            "availability",
            "shortname",
            "board",
            "names",
            "descriptions",
            "boards",
            "min_price",
            "max_price",
            "rtype",
            "woodoo",
        ]
        data = dict(list(zip(fields, args)))
        lcode = data["lcode"]
        rid = data[self._id]
        for k in self._meta_fields:
            del data[k]
        if lcode not in self.data:
            return -1, "The property '%s' does not exist" % lcode
        if rid not in self.data[lcode]:
            return -2, "The room type '{}' does not exist on property '{}'".format(
                rid,
                lcode,
            )
        res, info = self._check_unique_keys(lcode, data, exclude=True)
        if res:
            return res, info
        self.data[lcode][rid].update(data)
        return 0, None

    # aux methods
    def _check_unique_keys(self, lcode, data, exclude=False):
        dict_unique = {}
        for ukn, ukf in self._unique_keys.items():
            dict_unique.setdefault(ukn, tuple())
            dict_unique[ukn] = (tuple(ukf), tuple([data[x] for x in ukf]))
        records = self.data[lcode]
        if exclude:
            records = dict(records)
            del records[data[self._id]]
        for rec in records.values():
            for ukn, (ukf, ukv) in dict_unique.items():
                if tuple([rec[x] for x in ukf]) == ukv:
                    return (
                        -1,
                        "Duplicate values on property '%s': unique key '%s' -> '%s'"
                        % (lcode, ukn, ukv),
                    )
        return 0, None

    def get_mock(self):
        m = mock.Mock(
            spec=[
                "acquire_token",
                "release_token",
                "fetch_rooms",
                "fetch_single_room",
                "new_room",
                "mod_room",
            ]
        )

        m.acquire_token.return_value = (0, None)
        m.release_token.return_value = (0, None)

        m.fetch_rooms = self.fetch_rooms_mock
        m.fetch_single_room = self.fetch_single_room_mock

        m.new_room = self.new_room_mock
        m.mod_room = self.mod_room_mock

        return m


class TestWubookConnector(SavepointComponentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                test_queue_job_no_delay=True,  # no jobs thanks
            )
        )
