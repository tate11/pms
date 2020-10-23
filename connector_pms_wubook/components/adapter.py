# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import xmlrpc.client

from odoo import _

from odoo.addons.component.core import AbstractComponent
from odoo.addons.connector_pms.components.adapter import ChannelAdapterError


class ChannelWubookAdapter(AbstractComponent):
    _name = "channel.wubook.adapter"
    _inherit = ["channel.adapter", "base.channel.wubook.connector"]

    _id = "id"

    def __init__(self, environment):
        super().__init__(environment)

        self.url = self.backend_record.url
        self.username = self.backend_record.username
        self.password = self.backend_record.password
        self.apikey = self.backend_record.pkey
        self.property_code = self.backend_record.property_code

    def _exec(self, funcname, *args, **kwargs):
        s = xmlrpc.client.Server(self.url)
        res, token = s.acquire_token(self.username, self.password, self.apikey)
        if res:
            raise ChannelAdapterError(_("Error authorizing to endpoint. %s") % token)

        func = getattr(s, funcname)
        try:
            res, data = func(token, self.property_code, *args, **kwargs)
            if res:
                raise ChannelAdapterError(
                    _("Error executing function %s with params %s. %s")
                    % (funcname, args, data)
                )
            return data
        finally:
            # TODO: reutilize token on multiple calls
            res, info = s.release_token(token)
            if res:
                raise ChannelAdapterError(_("Error releasing token. %s") % info)

    def _prepare_field_type(self, field_data):
        default_values = {}
        fields = []
        for m in field_data:
            if isinstance(m, tuple):
                fields.append(m[0])
                default_values[m[0]] = m[1]
            else:
                fields.append(m)

        return fields, default_values

    def _prepare_parameters(self, values, mandatory, optional=None):
        if not optional:
            optional = []

        mandatory, mandatory_default_values = self._prepare_field_type(mandatory)
        optional, default_values = self._prepare_field_type(optional)

        default_values.update(mandatory_default_values)

        missing_fields = list(set(mandatory) - set(values))
        if missing_fields:
            raise ChannelAdapterError(_("Missing mandatory fields %s") % missing_fields)

        mandatory_values = [values[x] for x in mandatory]

        optional_values = []
        found = False
        for o in optional[::-1]:
            if not found and o in values:
                found = True
            if found:
                optional_values.append(values.get(o, default_values.get(o, False)))

        return mandatory_values + optional_values[::-1]

    def _filter(self, values, domain=None):
        # TODO support more cases
        # TODO refactor
        if not domain:
            return values

        if len(domain) > 1:
            raise NotImplementedError("Only one condition allowed for now")

        values_filtered = []
        for record in values:
            k, op, v = domain[0]
            if k not in record:
                raise Exception("Key %s does not exist" % k)
            if op == "=":
                if record[k] == v:
                    values_filtered.append(record)
            else:
                raise NotImplementedError("Operation %s not yet implemented" % op)

        return values_filtered
