def update_model_instance(instance: any, data: dict):
    for key, value in data.items():
        setattr(instance, key, value)
    return instance
