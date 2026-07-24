#!/usr/bin/env python3
import yaml
import os
import threading

class LandmarkSaver:
    def __init__(self, filepath):
        self.filepath = filepath
        self.lock = threading.Lock()
        self.landmarks = self._load_landmarks()

    def _load_landmarks(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                data = yaml.safe_load(f)
                if data is None:
                    return {}
                return data
        else:
            return {}

    def save_landmark(self, name, x, y, yaw):
        with self.lock:
            self.landmarks[name] = {'x': x, 'y': y, 'yaw': yaw}
            with open(self.filepath, 'w') as f:
                yaml.safe_dump(self.landmarks, f)

    def get_landmarks(self):
        with self.lock:
            return dict(self.landmarks)

