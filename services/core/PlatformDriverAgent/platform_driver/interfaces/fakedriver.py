import random
import datetime
import math
from math import pi


from csv import DictReader
from io import StringIO
import logging

from services.core.PlatformDriverAgent.platform_driver.interfaces import BaseRegister, BasicRevert, BaseInterface

_log = logging.getLogger(__name__)
type_mapping = {"string": str,
                "int": int,
                "integer": int,
                "float": float,
                "bool": bool,
                "boolean": bool}


class FakeRegister(BaseRegister):
    def __init__(self, read_only, pointName, units, reg_type,
                 default_value=None, description='', datetime_value=None):
        super(FakeRegister, self).__init__("byte", read_only, pointName, units,
                                           description='')
        self.reg_type = reg_type

        if pointName.lower() == "datetime":
            self.value = datetime_value
        elif default_value is None:
            self.value = self.reg_type(random.uniform(0, 100))
        else:
            try:
                self.value = self.reg_type(default_value)
            except ValueError:
                self.value = self.reg_type()


class EKGregister(BaseRegister):
    def __init__(self, read_only, pointName, units, reg_type,
                 default_value=None, description=''):
        super(EKGregister, self).__init__("byte", read_only, pointName, units,
                                          description='')
        self._value = 1;

        math_functions = ('acos', 'acosh', 'asin', 'asinh', 'atan', 'atan2',
                          'atanh', 'sin', 'sinh', 'sqrt', 'tan', 'tanh')
        if default_value in math_functions:
            self.math_func = getattr(math, default_value)
        else:
            _log.error('Invalid default_value in EKGregister.')
            _log.warning('Defaulting to sin(x)')
            self.math_func = math.sin

    @property
    def value(self):
        now = datetime.datetime.now()
        seconds_in_radians = pi * float(now.second) / 30.0

        yval = self.math_func(seconds_in_radians)

        return self._value * yval

    @value.setter
    def value(self, x):
        self._value = x


class Interface(BasicRevert, BaseInterface):
    def __init__(self, **kwargs):
        super(Interface, self).__init__(**kwargs)

    def configure(self, config_dict, registry_config_str):
        self.parse_config(registry_config_str)

    def get_point(self, point_name):
        register = self.get_register_by_name(point_name)
        return register.value

    def _set_point(self, point_name, value):
        register = self.get_register_by_name(point_name)
        if register.read_only:
            raise RuntimeError(
                "Trying to write to a point configured read only: " + point_name)

        register.value = register.reg_type(value)
        return register.value

    def _scrape_all(self):
        result = {}
        read_registers = self.get_registers_by_type("byte", True)
        write_registers = self.get_registers_by_type("byte", False)
        for register in read_registers + write_registers:
            result[register.point_name] = register.value

        return result

    def parse_config(self, configDict):
        if configDict is None:
            return

        for regDef in configDict:
            # Skip lines that have no address yet.
            if not regDef['Point Name']:
                continue

            read_only = regDef['Writable'].lower() != 'true'
            point_name = regDef['Volttron Point Name']
            description = regDef.get('Notes', '')
            units = regDef['Units']
            default_value = regDef.get("Starting Value", 'sin').strip()
            if not default_value:
                default_value = None
            type_name = regDef.get("Type", 'string')
            reg_type = type_mapping.get(type_name, str)

            datetime_value = regDef.get("DateTime", None)

            register_type = FakeRegister if not point_name.startswith('EKG') else EKGregister

            register = register_type(
                read_only,
                point_name,
                units,
                reg_type,
                default_value=default_value,
                description=description,
                datetime_value=datetime_value)

            if default_value is not None:
                self.set_default(point_name, register.value)

            self.insert_register(register)
