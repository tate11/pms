##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2018 -2021 Alda Hotels <informatica@aldahotels.com>
#                       Jose Luis Algara <osotranquilo@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import json
import logging
from datetime import date, datetime, timedelta

from odoo import _, api, models

_logger = logging.getLogger(__name__)

#
# def inv_percent_inc(amount, percent):
#     """Return the amount to which a percentage was increment applied."""
#     return amount - (amount * (100 - percent)) / 100
#
#
# def inv_percent(amount, percent):
#     """Return the amount to which a percentage was applied."""
#     return amount / ((100 - percent) / 100)


class DataBi(models.Model):
    """Management and export data for MopSolution MyDataBI."""
    _name = "data_bi"

    @api.model
    def export_data_bi(self,
                       archivo=0,
                       property=False,
                       fechafoto=date.today().strftime("%Y-%m-%d")):
        u"""Prepare a Json Objet to export data for MyDataBI.

        Generate a dicctionary to by send in JSON
        archivo = response file type
            archivo == 0 'ALL'
            archivo == 1 'Tarifa'
            archivo == 2 'Canal'
            archivo == 3 'Hotel'
            archivo == 4 'Pais'
            archivo == 5 'Regimen'
            archivo == 6 'Reservas'
            archivo == 7 'Capacidad'
            archivo == 8 'Tipo Habitación'
            archivo == 9 'Budget'
            archivo == 10 'Bloqueos'
            archivo == 11 'Motivo Bloqueo'
            archivo == 12 'Segmentos'
            archivo == 13 'Clientes'
            archivo == 14 'Estado Reservas'
            archivo == 15 'Room names'
        fechafoto = start date to take data
        """
        _logger.warning("--- ### Init Export Data_Bi Module parameters:  %s, %s, %s ### ---",
                        archivo,
                        property,
                        fechafoto)

        if type(fechafoto) is dict:
            fechafoto = date.today()
        else:
            fechafoto = datetime.strptime(fechafoto, "%Y-%m-%d").date()

        propertys = self.env['pms.property'].search([])
        if type(property) is int:
            property = self.env['pms.property'].search([('id', '=', property)])
            if len(property) == 1:
                propertys = property

        dias = self.env.user.data_bi_days
        limit_ago = (fechafoto - timedelta(days=dias)).strftime("%Y-%m-%d")

        _logger.info("Export Data %s days ago. From %s",dias, limit_ago)
        estado_array = ["draft", "confirm", "onboard", "done",
                        "cancelled", "no_show", "no_checkout"]

        dic_export = []  # Diccionario con lo necesario para exportar.

        # for property in propertys:
        #     _logger.warning("--- ### %s ### ---", property.name)

        if (archivo == 0) or (archivo == 1):
            dic_tarifa = self.data_bi_tarifa(propertys)
            dic_export.append({"Tarifa": dic_tarifa})

        if (archivo == 0) or (archivo == 2):
            dic_canal = self.data_bi_canal(propertys)
            dic_export.append({"Canal": dic_canal})

        if (archivo == 0) or (archivo == 3):
            dic_hotel = self.data_bi_hotel()
            dic_export.append({"Hotel": dic_hotel})

        if (archivo == 0) or (archivo == 4):
            dic_pais = self.data_bi_pais(propertys)
            dic_export.append({"Pais": dic_pais})

        if (archivo == 0) or (archivo == 5):
            dic_regimen = self.data_bi_regimen(propertys)
            dic_export.append({"Regimen": dic_regimen})

        if (archivo == 0) or (archivo == 10) or (archivo == 6):
            line_res = self.env["pms.reservation.line"].search(
                [("date", ">=", limit_ago)], order="id")

        if (archivo == 0) or (archivo == 6):
            dic_reservas = self.data_bi_reservas(
                propertys,
                line_res,
                estado_array,
            )
            dic_export.append({"Reservas": dic_reservas})

        if (archivo == 0) or (archivo == 7):
            dic_capacidad = self.data_bi_capacidad(propertys)
            dic_export.append({"Capacidad": dic_capacidad})

        if (archivo == 0) or (archivo == 8):
            dic_tipo_habitacion = self.data_bi_habitacione(propertys)
            dic_export.append({"Tipo Habitación": dic_tipo_habitacion})

        if (archivo == 0) or (archivo == 9):
            dic_budget = self.data_bi_budget(propertys)
            dic_export.append({"Budget": dic_budget})

        if (archivo == 0) or (archivo == 10):
            dic_bloqueos = self.data_bi_bloqueos(propertys, line_res)
            dic_export.append({"Bloqueos": dic_bloqueos})

        if (archivo == 0) or (archivo == 11):
            dic_moti_bloq = self.data_bi_moti_bloq(propertys)
            dic_export.append({"Motivo Bloqueo": dic_moti_bloq})

        if (archivo == 0) or (archivo == 12):
            dic_segmentos = self.data_bi_segment(propertys)
            dic_export.append({"Segmentos": dic_segmentos})

        if (archivo == 0) or (archivo == 13):
            dic_clientes = self.data_bi_client(propertys)
            dic_export.append({"Clientes": dic_clientes})

        if (archivo == 0) or (archivo == 14):
            dic_estados = self.data_bi_estados(propertys, estado_array)
            dic_export.append({"Estado Reservas": dic_estados})

        if (archivo == 0) or (archivo == 15):
            dic_rooms = self.data_bi_rooms(propertys)
            dic_export.append({"Nombre Habitaciones": dic_rooms})

        dictionary_to_json = json.dumps(dic_export)
        _logger.warning("--- ### End Export Data_Bi Module to Json ### ---")
        return dictionary_to_json

    @api.model
    def data_bi_tarifa(self, propertys):
        # Diccionario con las tarifas [1]
        dic_tarifa = []
        # tarifas = self.env["product.pricelist"].search_read(
        #     ["|", ("active", "=", False), ("active", "=", True)], ["name"])
        for property in propertys:
            tarifas = self.env["product.pricelist"].search_read(
                ["|", ("active", "=", False), ("active", "=", True), "|",
                 ('pms_property_ids', '=', property.id), ('pms_property_ids', '=', False)], ["name"])
            _logger.info("DataBi: Calculating %s fees in %s", str(len(tarifas)), property.name)
            for tarifa in tarifas:
                dic_tarifa.append(
                    {
                        "ID_Hotel": property.id,
                        "ID_Tarifa": tarifa["id"],
                        "Descripcion": tarifa["name"],
                    }
                )
        return dic_tarifa

    @api.model
    def data_bi_canal(self, propertys):
        # Diccionario con los Canales [2]
        dic_canal = []
        channels = self.env['pms.sale.channel'].search([])
        _logger.info("DataBi: Calculating %s Channels", str(len(channels)))
        for property in propertys:
            dic_canal.append({'ID_Hotel': property.id,
                              'ID_Canal': "0",
                              'Descripcion': u'Ninguno'})
            for channel in channels:
                dic_canal.append({'ID_Hotel': property.id,
                                  'ID_Canal': channel['id'],
                                  'Descripcion': channel['name']
                                  })
        return dic_canal

    @api.model
    def data_bi_hotel(self):
        # Diccionario con el/los nombre de los hoteles  [3]
        hoteles = self.env['pms.property'].search([])
        _logger.info("DataBi: Calculating %s hotel names", str(len(hoteles)))

        dic_hotel = []
        for hotel in hoteles:
            dic_hotel.append({"ID_Hotel": hotel.id,
                              "Descripcion": hotel.name})
        return dic_hotel

    @api.model
    def data_bi_pais(self, propertys):
        dic_pais = []
        # Diccionario con los nombre de los Paises usando los del INE [4]
        paises = self.env['code.ine'].search_read([], ['code', 'name'])
        _logger.info("DataBi: Calculating %s countries", str(len(paises)))
        for property in propertys:
            dic_pais.append({'ID_Hotel': property.id,
                             'ID_Pais': 'NONE',
                             'Descripcion': 'No Asignado'})
            for pais in paises:
                dic_pais.append({'ID_Hotel': property.id,
                                 'ID_Pais': pais['code'],
                                 'Descripcion': pais['name']})
        return dic_pais

    @api.model
    def data_bi_regimen(self, propertys):
        # Diccionario con los Board Services [5]
        dic_regimen = []
        board_services = self.env['pms.board.service'].search_read([])
        _logger.info("DataBi: Calculating %s board services", str(
            len(board_services)))
        for property in propertys:
            dic_regimen.append({'ID_Hotel': property.id,
                                'ID_Regimen': 0,
                                'Descripcion': u'Sin régimen'})
            for board_service in board_services:
                if (not board_service['pms_property_ids']) or (
                        property.id in board_service['pms_property_ids']):
                    dic_regimen.append({'ID_Hotel': property.id,
                                        'ID_Regimen': board_service['id'],
                                        'Descripcion': board_service['name']})
        return dic_regimen

    @api.model
    def data_bi_capacidad(self, propertys):
        # Diccionario con las capacidades  [7]
        rooms = self.env["pms.room.type"].search_read([])
        _logger.info("DataBi: Calculating %s room capacity", str(len(rooms)))
        dic_capacidad = []
        for property in propertys:
            for room in rooms:
                if (not room['pms_property_ids']) or (
                        property.id in room['pms_property_ids']):
                    dic_capacidad.append({
                        'ID_Hotel': property.id,
                        'Hasta_Fecha':
                            (date.today() + timedelta(days=365 * 3)).strftime("%Y-%m-%d"),
                        'ID_Tipo_Habitacion': room['id'],
                        'Nro_Habitaciones': room['total_rooms_count']})
        return dic_capacidad

    @api.model
    def data_bi_habitacione(self, propertys):
        # Diccionario con Rooms types [8]
        rooms = self.env["pms.room.type"].search([])
        _logger.info("DataBi: Calculating %s room types", str(len(rooms)))
        dic_tipo_habitacion = []
        for property in propertys:
            for room in rooms:
                if (not room.pms_property_ids) or (
                        property.id in room.pms_property_ids.ids):
                    dic_tipo_habitacion.append({
                        'ID_Hotel': property.id,
                        'ID_Tipo_Habitacion': room['id'],
                        'Descripcion': room['name'],
                        'Estancias': room.get_capacity()})
        return dic_tipo_habitacion

    @api.model
    def data_bi_budget(self, propertys):
        # Diccionario con las previsiones Budget [9]
        budgets = self.env['pms.budget'].search([])
        _logger.info("DataBi: Calculating %s budget", str(len(budgets)))
        dic_budget = []
        for property in propertys:
            for budget in budgets:
                if budget.pms_property_id.id == property.id:
                    dic_budget.append({'ID_Hotel': property.id,
                                       'Fecha': str(budget.year) + '-' +
                                                str(budget.month).zfill(2) + '-01',
                                       # 'ID_Tarifa': 0,
                                       # 'ID_Canal': 0,
                                       # 'ID_Pais': 0,
                                       # 'ID_Regimen': 0,
                                       # 'ID_Tipo_Habitacion': 0,
                                       # 'ID_Cliente': 0,
                                       'Room_Nights': budget.room_nights,
                                       'Room_Revenue': budget.room_revenue,
                                       # 'Pension_Revenue': 0,
                                       'Estancias': budget.estancias})
            # Fecha fecha Primer día del mes
            # ID_Tarifa numérico Código de la Tarifa
            # ID_Canal numérico Código del Canal
            # ID_Pais numérico Código del País
            # ID_Regimen numérico Cóigo del Régimen
            # ID_Tipo_Habitacion numérico Código del Tipo de Habitación
            # iD_Segmento numérico Código del Segmento
            # ID_Cliente numérico Código del Cliente
            # Pension_Revenue numérico con dos decimales Ingresos por Pensión
        return dic_budget

    @api.model
    def data_bi_moti_bloq(self, propertys):
        # Diccionario con Motivo de Bloqueos [11]
        lineas = self.env['room.closure.reason'].search([])
        dic_moti_bloq = []
        _logger.info("DataBi: Calculating %s blocking reasons", str(len(lineas)))
        for property in propertys:
            dic_moti_bloq.append({'ID_Hotel': property.id,
                                  'ID_Motivo_Bloqueo': "B0",
                                  'Descripcion': u'Ninguno'})
            dic_moti_bloq.append({'ID_Hotel': property.id,
                                  'ID_Motivo_Bloqueo': "ST",
                                  'Descripcion': u'Staff'})
            for linea in lineas:
                if (not linea.pms_property_ids) or (
                        property.id in linea.pms_property_ids.ids):
                    dic_moti_bloq.append({'ID_Hotel': property.id,
                                          'ID_Motivo_Bloqueo': "B"+str(linea.id),
                                          'Descripcion': linea.name})
        return dic_moti_bloq

    @api.model
    def data_bi_segment(self, propertys):
        # Diccionario con Segmentación [12]
        # TODO solo las que tienen un padre?... ver la gestion... etc....
        dic_segmentos = []
        lineas = self.env['res.partner.category'].search([])
        _logger.info("DataBi: Calculating %s segmentations", str(len(lineas)))
        for property in propertys:
            for linea in lineas:
                if linea.parent_id.name:
                    seg_desc = linea.parent_id.name + " / " + linea.name
                    dic_segmentos.append({'ID_Hotel': property.id,
                                          'ID_Segmento': linea.id,
                                          'Descripcion': seg_desc})
        return dic_segmentos

    @api.model
    def data_bi_client(self, propertys):
        # Diccionario con Clientes (OTAs y agencias) [13]
        dic_clientes = []
        lineas = self.env['res.partner'].search([('is_agency', '=', True)])
        _logger.info("DataBi: Calculating %s Operators", str(len(lineas)))
        for property in propertys:
            dic_clientes.append({'ID_Hotel': property.id,
                                 'ID_Cliente': 0,
                                 'Descripcion': u'Ninguno'})
            for linea in lineas:
                dic_clientes.append({'ID_Hotel': property.id,
                                     'ID_Cliente': linea.id,
                                     'Descripcion': linea.name})
        return dic_clientes

    # @api.model
    # def get_data_bi_client(self, linea, dic_clientes):
    #     # return client in linea
    #     cliente = 0
    #     if linea.reservation_id.agency_id.name:
    #         cliente = next((sub for sub in dic_clientes if sub['Descripcion'] == linea.reservation_id.agency_id.name), None)
    #         cliente = cliente['ID_Cliente']
    #     if linea.reservation_id.channel_type_id.name:
    #         cliente = next((sub for sub in dic_clientes if sub['Descripcion'] == linea.reservation_id.channel_type_id.name),
    #                        None)
    #
    #     return '0' if cliente == 0 else cliente['ID_Cliente']

    # def data_bi_client(self, property_id):
    #     # Diccionario con Clientes (OTAs y agencias)
    #     dic_clientes = [{'ID_Hotel': property_id,
    #                      'ID_Cliente': 0,
    #                      'Descripcion': u'Ninguno'}]
    #     lineas = self.env['channel.ota.info'].search([])
    #     _logger.info("DataBi: Calculating %s otas", str(len(lineas)))
    #
    #     for linea in lineas:
    #         dic_clientes.append({'ID_Hotel': property_id,
    #                              'ID_Cliente': linea.id,
    #                              'Descripcion': linea.name})
    #
    #     lineas = self.env['res.partner'].search([('is_tour_operator',
    #                                             '=', True)])
    #     id_cli_count = 700
    #     _logger.info("DataBi: Calculating %s Operators", str(len(lineas)))
    #     for linea in lineas:
    #         dic_clientes.append({'ID_Hotel': property_id,
    #                              'ID_Cliente': id_cli_count,
    #                              'Descripcion': linea.name})
    #         id_cli_count += 1
    #
    #     dic_clientes.append({'ID_Hotel': property_id,
    #                          'ID_Cliente': 999,
    #                          'Descripcion': u'Web Propia'})
    #     dic_clientes.append({'ID_Hotel': property_id,
    #                          'ID_Cliente': 901,
    #                          'Descripcion': u'Expedia Empaquedata'})
    #     dic_clientes.append({'ID_Hotel': property_id,
    #                          'ID_Cliente': 902,
    #                          'Descripcion': u'Expedia Sin Comisión'})
    #     dic_clientes.append({'ID_Hotel': property_id,
    #                          'ID_Cliente': 903,
    #                          'Descripcion': u'Puerta'})
    #     dic_clientes.append({'ID_Hotel': property_id,
    #                          'ID_Cliente': 904,
    #                          'Descripcion': u'E-Mail'})
    #     dic_clientes.append({'ID_Hotel': property_id,
    #                          'ID_Cliente': 905,
    #                          'Descripcion': u'Teléfono'})
    #     dic_clientes.append({'ID_Hotel': property_id,
    #                          'ID_Cliente': 906,
    #                          'Descripcion': u'Call Center'})
    #     dic_clientes.append({'ID_Hotel': property_id,
    #                          'ID_Cliente': 907,
    #                          'Descripcion': u'Agencia'})
    #     dic_clientes.append({'ID_Hotel': property_id,
    #                          'ID_Cliente': 908,
    #                          'Descripcion': u'Touroperador'})
    #     dic_clientes.append({'ID_Hotel': property_id,
    #                          'ID_Cliente': 909,
    #                          'Descripcion': u'Virtual Door'})
    #     dic_clientes.append({'ID_Hotel': property_id,
    #                          'ID_Cliente': 910,
    #                          'Descripcion': u'Desvío'})
    #     return dic_clientes

    @api.model
    def data_bi_estados(self, propertys, estado_array):
        # Diccionario con los Estados Reserva [14]
        _logger.info("DataBi: Calculating states of the reserves")
        dic_estados = []
        estado_array_txt = ['Borrador', 'Confirmada', 'Hospedandose',
                            'Checkout', 'Cancelada', 'No Show', 'No Checkout']
        for property in propertys:
            for i in range(0, len(estado_array)):
                dic_estados.append({'ID_Hotel': property.id,
                                    'ID_EstadoReserva': str(i),
                                    'Descripcion': estado_array_txt[i]})
        return dic_estados

    @api.model
    def data_bi_rooms(self, propertys):
        # Diccionario con las habitaciones [15]
        dic_rooms = []
        rooms = self.env['pms.room'].search([])
        _logger.info("DataBi: Calculating %s name rooms.", str(len(rooms)))
        for property in propertys:
            for room in rooms.filtered(lambda n: (n.pms_property_id.id == property.id)):
                dic_rooms.append({'ID_Hotel': property.id,
                                  'ID_Room': room.id,
                                  'Descripcion': room.name})
        return dic_rooms

    @api.model
    def data_bi_bloqueos(self, propertys, lines):
        # Diccionario con Bloqueos [10]
        dic_bloqueos = []
        lines = lines.filtered(
            lambda n: (n.reservation_id.reservation_type != 'normal') and (
                n.reservation_id.state != 'cancelled'))
        _logger.info("DataBi: Calculating %s Bloqued", str(len(lines)))
        for line in lines:

            if line.pms_property_id.id in propertys.ids:
                motivo = "0"
                if line.reservation_id.reservation_type == 'out':
                    motivo = "B0" if not line.reservation_id.closure_reason_id.id else (
                        "B"+str(line.reservation_id.closure_reason_id.id))

                elif line.reservation_id.reservation_type == 'staff':
                    motivo = "ST"
                dic_bloqueos.append({
                    'ID_Hotel': line.pms_property_id.id,
                    'Fecha_desde': line.date.strftime("%Y-%m-%d"),
                    'Fecha_hasta': (line.date + timedelta(days=1)).strftime("%Y-%m-%d"),
                    'ID_Tipo_Habitacion': line.reservation_id.room_type_id.id,
                    'ID_Motivo_Bloqueo': motivo,
                    'Nro_Habitaciones': 1})
        return dic_bloqueos

    @api.model
    def data_bi_reservas(self, propertys, lines, estado_array):
        # Diccionario con Reservas  [6]
        dic_reservas = []

        for property in propertys:
            lineas = lines.filtered(lambda n: (n.pms_property_id.id == property.id) and
                                              (n.reservation_id.reservation_type == 'normal') and
                                              (n.price > 0))
            _logger.info("DataBi: Calculating %s reservations in %s ", str(len(lineas)), property.name)

            for linea in lineas:
                if linea.reservation_id.segmentation_ids:
                    id_segmen = linea.reservation_id.segmentation_ids[0].id
                elif linea.reservation_id.folio_id.segmentation_ids:
                    id_segmen = linea.reservation_id.folio_id.segmentation_ids[0].id
                else:
                    id_segmen = 0

                regimen = 0 if not linea.reservation_id.board_service_room_id else \
                    linea.reservation_id.board_service_room_id.id

                cuna = 0
                for service in linea.reservation_id.service_ids:
                    if service.product_id.is_crib:
                        cuna += 1

                canal = linea.reservation_id.channel_type_id.id if \
                    linea.reservation_id.channel_type_id.id else 0

                cliente = linea.reservation_id.agency_id.id if \
                    linea.reservation_id.agency_id.id else 0

                dic_reservas.append({
                    'ID_Reserva': linea.reservation_id.folio_id.id,
                    'ID_Hotel': property.id,
                    'ID_EstadoReserva': estado_array.index(
                        linea.reservation_id.state),
                    'FechaVenta': linea.reservation_id.create_date.strftime('%Y-%m-%d'),
                    'ID_Segmento': id_segmen,
                    'ID_Cliente': cliente,
                    'ID_Canal': canal,
                    'FechaExtraccion': date.today().strftime('%Y-%m-%d'),
                    'Entrada': linea.date.strftime('%Y-%m-%d'),
                    'Salida': (linea.date + timedelta(days=1)).strftime("%Y-%m-%d"),
                    'Noches': 1,
                    'ID_TipoHabitacion': linea.reservation_id.room_type_id.id,
                    'ID_HabitacionDuerme': linea.room_id.room_type_id.id,
                    'ID_Regimen': regimen,
                    'Adultos': linea.reservation_id.adults,
                    'Menores': linea.reservation_id.children,
                    'Cunas': cuna,
                    # TODO Precios y comisiones por noche
                    # 'PrecioDiario': precio_neto,
                    # 'PrecioComision': precio_comision,
                    # 'PrecioIva': precio_iva,
                    # 'PrecioDto': precio_dto,
                    'ID_Tarifa': linea.reservation_id.pricelist_id.id,
                    'ID_Pais': self.data_bi_get_codeine(linea),
                    'ID_Room': linea.room_id.id,
                    'FechaCancelacion': "NONE",
                    'ID_Folio': linea.reservation_id.folio_id.name,
                })
                if linea.reservation_id.state == 'cancelled':
                    dic_reservas[-1]['FechaCancelacion'] = \
                        linea.reservation_id.write_date.strftime('%Y-%m-%d')
                    # _logger.info("DataBi: %s CANCELADA %s",
                    #              dic_reservas[-1]['Entrada'],
                    #              dic_reservas[-1]['ID_Folio'])
                # ID_Reserva numérico Código único de la reserva
                # ID_Hotel numérico Código del Hotel
                # ID_EstadoReserva numérico Código del estado de la reserva
                # FechaVenta fecha Fecha de la venta de la reserva
                # ID_Segmento numérico Código del Segmento de la reserva
                # ID_Cliente Numérico Código del Cliente de la reserva
                # ID_Canal numérico Código del Canal
                # FechaExtraccion fecha Fecha de la extracción de los datos (Foto)
                # Entrada fecha Fecha de entrada
                # Salida fecha Fecha de salida
                # Noches numérico Nro. de noches de la reserva
                # ID_TipoHabitacion numérico Código del Tipo de Habitación
                # ID_Regimen numérico Código del Tipo de Régimen
                # Adultos numérico Nro. de adultos
                # Menores numérico Nro. de menores
                # Cunas numérico Nro. de cunas
                # PrecioDiario numérico con 2 decimales Precio por noche de la reserva
                # ID_Tarifa numérico Código de la tarifa aplicada a la reserva
                # ID_Pais alfanumérico Código del país

        return dic_reservas

    @api.model
    def data_bi_get_codeine(self, reserva):
        response = 'NONE'
        if reserva.reservation_id.partner_id.code_ine_id:
            response = reserva.reservation_id.partner_id.code_ine_id.code
        else:
            for l in reserva.reservation_id.folio_id.checkin_partner_ids:
                if l.partner_id.code_ine_id.code:
                    response = l.partner_id.code_ine_id.code
        return response
