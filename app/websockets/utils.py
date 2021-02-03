from django.forms import model_to_dict

from app.websockets.models import Notification


def notification_to_json(notification):
    data = model_to_dict(notification, exclude=['users'])
    data['action_path'] = Notification.get_section_choices_label_value(data['action_path'])
    return data
