"""Stub implementation of DMCLIAPI"""

class DMCLIAPI:
    def __init__(self, *args, **kwargs):
        pass
    
    def __getattr__(self, name):
        def stub_method(*args, **kwargs):
            return None
        return stub_method

