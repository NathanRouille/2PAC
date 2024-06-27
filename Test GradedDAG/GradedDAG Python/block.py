class block:
    def __init__(self, index, data):
        self.index = index
        self.data = data

    def __getstate__(self):
        # Return a dictionary containing the state of the object
        return {
            'index': self.index,
            'data': self.data,
        }

    def __setstate__(self, state):
        # Restore the state of the object from the dictionary
        self.index = state['index']
        self.data = state['data']

