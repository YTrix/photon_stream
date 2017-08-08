from .Event import Event
from .JsonLinesGzipReader import JsonLinesGzipReader
from .simulation_truth.corsika_headers import read_corsika_headers
from .simulation_truth.corsika_headers import IDX_RUNH_RUN_NUMBER
from .simulation_truth.corsika_headers import IDX_EVTH_EVENT_NUMBER
from .simulation_truth.corsika_headers import IDX_EVTH_REUSE_NUMBER
from .simulation_truth.corsika_headers import IDX_EVTH_RUN_NUMBER
from .simulation_truth.AirShowerTruth import AirShowerTruth
import numpy as np


class SimulationReader(object):
    '''
    Reads in both simulated photon-stream events and MMCS CORSIKA run and event
    headers. Returns merged events with full and raw CORSIKA simulation truth. 
    '''
    def __init__(self, photon_stream_path, mmcs_corsika_path):
        self.reader = JsonLinesGzipReader(photon_stream_path)
        self.mmcs_corsika_path = mmcs_corsika_path
        mmcs_corsika_headers = read_corsika_headers(mmcs_corsika_path)
        self.run_header = mmcs_corsika_headers['run_header']
        self.event_headers = mmcs_corsika_headers['event_headers']
        self.id_to_index = {}
        for idx in range(self.event_headers.shape[0]):
            event_id = self.event_headers[idx][IDX_EVTH_EVENT_NUMBER]
            reuse_id = self.event_headers[idx][IDX_EVTH_REUSE_NUMBER]
            self.id_to_index[(event_id, reuse_id)] = idx
        self.event_passed_trigger = np.zeros(self.event_headers.shape[0], dtype=np.bool8)


    def __iter__(self):
        return self

    def __next__(self):
        event = Event.from_event_dict(next(self.reader))
        assert event.simulation_truth.run == self.run_header[IDX_RUNH_RUN_NUMBER]
    
        idx = self.id_to_index[(event.simulation_truth.event, event.simulation_truth.reuse)]

        assert event.simulation_truth.run == self.event_headers[idx][IDX_EVTH_RUN_NUMBER]
        assert event.simulation_truth.event == self.event_headers[idx][IDX_EVTH_EVENT_NUMBER]
        assert event.simulation_truth.reuse == self.event_headers[idx][IDX_EVTH_REUSE_NUMBER]
        self.event_passed_trigger[idx] = True

        event.simulation_truth.air_shower =  AirShowerTruth(
            raw_corsika_run_header=self.run_header, 
            raw_corsika_event_header=self.event_headers[idx]
        )

        return event

    def __repr__(self):
        out = 'SimulationsReader('
        out += "photon-stream '" + self.reader.path + "', "
        out += "CORSIKA '" + self.mmcs_corsika_path + "'"
        out += ')\n'
        return out