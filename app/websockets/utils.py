from django.forms import model_to_dict


def notification_to_json(notification):
    data = model_to_dict(notification, exclude=['users'])
    return data
