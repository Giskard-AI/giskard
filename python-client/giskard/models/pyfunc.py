from giskard.models.base.serialization import CloudpickleSerializableModel


class PyFuncModel(CloudpickleSerializableModel):
    def model_predict(self, df):
        return self.model.predict(df)
