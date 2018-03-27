from flask import jsonify

from werkzeug.utils import secure_filename

from file_data_injector_thread import ThreadClass

import os

import errors

ERROR_FILE_NAME = "error_dump"

from state import SingletonState

from threading import Lock


class RequestHandler:
    
    def __init__(self):

        self.state = SingletonState.instance()
        self.mapping_lock = Lock()
        self.data_lock = Lock()

    def get_state(self):

        return jsonify({"state": self.state.get_state()})

    def get_error(self):

        self.state.verify_modify_state('CRASHED', 'AVAILABLE')

        if not os.path.exists(os.path.join('.', ERROR_FILE_NAME)):
            return errors.no_error_file_generated()

        with open(ERROR_FILE_NAME, 'r') as error_file:
            content = error_file.read()

        return str(content), 200

    def set_mapping(self, request):

        with self.mapping_lock:

            if self.state.get_state() != 'AVAILABLE':
                return 'Injector not available'

            if 'mapping.json' not in request.files:
                return 'No mapping file provide'
            file = request.files['mapping.json']

            if file.filename == '':
                return 'No selected file'

            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join('', filename))

            return 'File accepted', 200

    def set_data(self, request):

        with self.data_lock:

            if self.state.get_state() != 'AVAILABLE':
                return 'Injector not available'

            if 'data.json' not in request.files:
                return 'No data file provide'
            file = request.files['data.json']

            if file.filename == '':
                return 'No selected file'

            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join('', filename))

            return 'File accepted', 200

    def start(self):

        if not self.state.verify_modify_state('AVAILABLE', 'RUNNING'):
            return 'Injector not available'

        thread = ThreadClass()
        thread.setDaemon(True)
        thread.start()

        return 'Injector launch', 200

    def resume(self):

        if not self.state.verify_modify_state('PAUSE', 'RUNNING'):
            return 'Injector not paused'

        thread = ThreadClass()
        thread.setDaemon(True)
        thread.start()

        return 'Injector unpaused', 200

    def stop(self):

        if not self.state.verify_modify_state('RUNNING', 'STOP'):
            return 'There is no injector to stop'

        return 'Injector thread stopped', 200

    def pause(self):

        if not self.state.verify_modify_state('RUNNING', 'PAUSE'):
            return 'There is no injector to pause'

        return 'Injector thread paused', 200