class Frame(object):
    # define a frame structure with probe requests object with two classifications directed probe requests and null probe requests
    def __init__(self):
        self.value = {'frame': {'probes': {'directed': [], 'null': []}}}
