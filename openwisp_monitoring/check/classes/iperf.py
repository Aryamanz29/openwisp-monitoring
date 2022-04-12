import subprocess

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from jsonschema import draft7_format_checker, validate
from jsonschema.exceptions import ValidationError as SchemaError
from swapper import load_model

from openwisp_utils.utils import deep_merge_dicts

from ... import settings as monitoring_settings
from .. import settings as app_settings
from ..exceptions import OperationalError
from .base import BaseCheck
from openwisp_controller.connection.tasks import launch_command

Chart = load_model('monitoring', 'Chart')
Metric = load_model('monitoring', 'Metric')
Device = load_model('config', 'Device')
DeviceData = load_model('device_monitoring', 'DeviceData')
Credentials = load_model('connection', 'Credentials')
AlertSettings = load_model('monitoring', 'AlertSettings')
Command = load_model('connection', 'Command')
DeviceConnection = load_model('connection', 'DeviceConnection')

class Iperf(BaseCheck):
    def check(self, store=True):
        # 192.168.5.109
        servers = list(app_settings.IPERF_SERVERS.values())[0][0]
        # Check device connection
        print('-------- DEBUG START ----------')
        try:
            device_connection = DeviceConnection.objects.get(device_id=self.related_object.id)
            if device_connection.enabled and device_connection.is_working:
                print(f'DEVICE IS CONNECTED, {self.related_object.id}')
                print()
                
            else:
                logger.warning(f'{self.related_object}: Connection not properly set')
                return
        # If device have not active connection warning logged (return)
        except ObjectDoesNotExist:
            return
        print('-------- DEBUG END ----------')
        pass

    def store_result(self, result):
        pass
    def _get_param(self, param):
        pass

    def _get_ip(self):
        pass
    def _command(self, command):
        pass
    def _get_metric(self):
       pass
    def _create_alert_settings(self, metric):
        pass
    def _create_charts(self, metric):
        pass