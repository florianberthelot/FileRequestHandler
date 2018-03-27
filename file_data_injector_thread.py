import os
import json
from ziggy_enabler import ziggyClient, converter, injector
from threading import Thread
import collections
import traceback
from state import SingletonState


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAPPING_PATH = os.path.join(BASE_DIR, "mapping.json")
DATA_PATH = os.path.join(BASE_DIR, "data.json")
NAMESPACE = "TEST_THREAD_INJECTOR"
API_ENDPOINT = "http://ziggy-api-dev.nprpaas.ddns.integ.dns-orange.fr/api/"
RECOVERY_PATH = os.path.join(BASE_DIR, "error")
ERROR_FILE_NAME = "error_dump"



class ThreadClass(Thread):

    def extract_subpart_dict(self, dict, first_element):
        return {k: dict[k] for k in list(dict.keys())[first_element:] if k in dict}

    def __init__(self):
        Thread.__init__(self)

    def run(self):
         self.inject()

    def inject(self):

        print("Inject")

        state = SingletonState.instance()

        try:

            if os.path.exists(MAPPING_PATH):
                try:
                    with open(os.path.join(MAPPING_PATH), "r") as f:
                        mapping = json.load(f)
                except Exception as e:
                    raise Exception('Failed to load mapping file as json.\n' + str(e))
            else:
                raise Exception('There is no mapping file')

            client = ziggyClient.ZiggyHTTPClient(NAMESPACE, API_ENDPOINT)
            manager = injector.DataManager(client, mapping)

            if os.path.exists(DATA_PATH):
                try:
                    with open(os.path.join(DATA_PATH), "r") as f:
                        data = json.load(f)
                except Exception as e:
                    raise Exception('Failed to load data file as json.\n' + str(e))

            else:
                raise Exception('There is no data file')

            conv = converter.JsonToRDFConverter(mapping)

            map_id_projections = collections.OrderedDict(sorted(conv.parse(data).items()))

            recovery_line = 0

            if os.path.exists(RECOVERY_PATH):

                f = open(str(RECOVERY_PATH), "r")
                recovery_line = int(f.readline())

                map_id_projections = collections.OrderedDict(
                    sorted(self.extract_subpart_dict(map_id_projections, recovery_line).items()))

                f.close()
                os.remove(RECOVERY_PATH)

            print("Process")

            manager.process_batch(map_id_projections, RECOVERY_PATH, begin_index=recovery_line)

            state.verify_modify_states(['RUNNING', 'STOP'], 'AVAILABLE')

        except Exception as e:
            print(traceback.print_exc())
            error_file = open(ERROR_FILE_NAME, "w")
            error_file.write(str(e))
            state.set_state('CRASHED')
                


