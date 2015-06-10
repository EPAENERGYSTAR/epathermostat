
# tuples of columns are "at least one of"
EQUIPMENT_TYPE_REQUIRED_COLUMNS = {
    0: [],
    1: ["ss_heat_pump_heating","ss_heat_pump_cooling",("auxiliary_heat","emergency_heat")],
    2: ["ss_heat_pump_heating","ss_heat_pump_cooling"],
    3: ["ss_heating","ss_central_ac"],
    4: ["ss_heating"],
    5: ["ss_central_ac"],
}

EQUIPMENT_TYPE_DISALLOWED_COLUMNS = {
    0: [],
    1: [],
    2: ["auxiliary_heat","emergency_heat"],
    3: [],
    4: ["ss_central_ac"],
    5: ["ss_heating"],
}

class Thermostat(object):

    def __init__(self,thermostat_id,equipment_type,
            temperature_in,temperature_setpoint,temperature_out,
            ss_heat_pump_heating=None,
            ss_heat_pump_cooling=None,
            auxiliary_heat=None,
            emergency_heat=None,
            ss_heating=None,
            ss_central_ac=None):

        self.thermostat_id = thermostat_id
        self.equipment_type = equipment_type
        self.temperature_in = temperature_in
        self.temperature_setpoint = temperature_setpoint
        self.temperature_out = temperature_out

        self._match_equipment_type_columns(
                ss_heat_pump_heating,
                ss_heat_pump_cooling,
                auxiliary_heat,
                emergency_heat,
                ss_heating,
                ss_central_ac)

    def _match_equipment_type_columns(self,
            ss_heat_pump_heating,
            ss_heat_pump_cooling,
            auxiliary_heat,
            emergency_heat,
            ss_heating,
            ss_central_ac):

        columns = {
                "ss_heat_pump_heating": ss_heat_pump_heating,
                "ss_heat_pump_cooling": ss_heat_pump_cooling,
                "auxiliary_heat": auxiliary_heat,
                "emergency_heat": emergency_heat,
                "ss_heating": ss_heating,
                "ss_central_ac": ss_central_ac
                }

        # Make sure we have a valid equipment type
        if not self.equipment_type in EQUIPMENT_TYPE_REQUIRED_COLUMNS.keys():
            message = "Unrecognized equipment_type. Should be one of {}"\
                    .format(EQUIPMENT_TYPE_REQUIRED_COLUMNS.keys())
            raise ValueError(message)

        # Make sure required columns are present, add them as attributes if
        # they are, and complain if they're not.
        for required_column in EQUIPMENT_TYPE_REQUIRED_COLUMNS[self.equipment_type]:
            if type(required_column) == tuple:
                if any([columns[column_name] is not None for column_name in required_column]):
                    for column_name in required_column:
                        self.__dict__[column_name] = columns[column_name]
                else:
                    message = ("The columns {} are missing, but at least one "
                               "of them must be supplied for equipment_type {}.")\
                            .format(required_column,self.equipment_type)
                    raise ValueError(message)
            else:
                if columns[required_column] is None:
                    message = ("The column '{}' is missing, but is required for "
                               "equipment_type {}.").format(required_column,self.equipment_type)
                    raise ValueError(message)
                else:
                    self.__dict__[required_column] = columns[required_column]

        # Make sure disallowed columns are not present and complain if they are.
        disallowed_columns = EQUIPMENT_TYPE_DISALLOWED_COLUMNS[self.equipment_type]
        for column_name, column in columns.iteritems():
            if column is not None and column_name in disallowed_columns:
                    message = ("The column '{}' is not allowed for"
                               "equipment type {}.").format(column_name,self.equipment_type)
                    raise ValueError(message)


