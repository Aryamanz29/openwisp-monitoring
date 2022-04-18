import subprocess

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from jsonschema import draft7_format_checker, validate
from jsonschema.exceptions import ValidationError as SchemaError
from swapper import load_model
import json
from openwisp_utils.utils import deep_merge_dicts

from ... import settings as monitoring_settings
from .. import settings as app_settings
from ..exceptions import OperationalError
from .base import BaseCheck
from openwisp_controller.connection.connectors.ssh import Ssh

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
        command = f'iperf3 -c {servers} -J'
        # Check device connection
        print('-------- DEBUG START ----------')
        try:
            device_connection = DeviceConnection.objects.get(device_id=self.related_object.id)
            if device_connection.enabled and device_connection.is_working:
                device_connection.connect()
                print(f'DEVICE IS CONNECTED, {self.related_object.id}') 
                res, exit_code = device_connection.connector_instance.exec_command(command, raise_unexpected_exit=False)
                if exit_code != 0:
                    print('---- Command Failed ----')
                    print(res[0], type(res))
                    return 
                else:
                    res_dict = self.get_res_data(res) 
                    print('---- Command Output ----')
                    print(res_dict, type(res_dict))
                    if store:
                        self.store_result(res_dict)
                    return res_dict    
            else:
                print(f'{self.related_object}: Connection not properly set')
                return
        # If device have not active connection warning logged (return)
        except ObjectDoesNotExist:
            return
        print('-------- DEBUG END ----------')
        pass

    def get_res_data(self, res, mode=None):
        res_loads = json.loads(res)
        if mode is None:
            result = {
            # 'host' : res_loads['start']['connecting_to']['host'],
            # 'port' : res_loads['start']['connecting_to']['port'],
            # 'protocol' : res_loads['start']['test_start']['protocol'],
            # 'duration' : res_loads['start']['test_start']['duration'],
            'iperf_result' : 1,
            # 'sum_sent_bytes' : res_loads['end']['sum_sent']['bytes'],
            'sum_sent_bps' : round(res_loads['end']['sum_sent']['bits_per_second']/1000000000,2),
            # 'sum_sent_retransmits' : res_loads['end']['sum_sent']['retransmits'],
            # 'sum_rec_bytes' : res_loads['end']['sum_received']['bytes'],
            'sum_rec_bps' : round(res_loads['end']['sum_received']['bits_per_second']/1000000000,2)
            }
            return result
        # For UDP
        else:
            pass

    def store_result(self, result):
        """
        store result in the DB
        """
        metric = self._get_metric()
        copied = result.copy()
        iperf_result = copied.pop('iperf_result')
        print(f"IPERF REACHABLE DICT == {iperf_result}, COPIED DICT == {copied}")
        print("STORE RESULT, Metric === ", print(metric.field_name))
        metric.write(iperf_result, extra_values=copied)
    
    def _get_metric(self):
        """
        Gets or creates metric
        """
        metric, created = self._get_or_create_metric()
        print('CREATED ====', created)
        if created:
            print("CREATING CHARTS")
            self._create_charts(metric)
        return metric

    def _create_charts(self, metric):
        """
        Creates Iperf related charts (Bandwith/Jitter)
        """
        charts = ['bps']
        print("RUNNING CHARTS", "METRIC === ", metric)
        for chart in charts:
            print("CREATING CHARTS == ", chart)
            chart = Chart(metric=metric, configuration=chart)
            chart.full_clean()
            chart.save()

    def _create_alert_settings(self, metric):
        pass