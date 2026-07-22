class CurrentProject:

    path = None


    @classmethod
    def set_project(cls, path):

        cls.path = path



    @classmethod
    def get_project(cls):

        return cls.path