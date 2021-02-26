from django.shortcuts import redirect
from django.urls import reverse_lazy

from app.websockets.models import Ticket, Chat, ChatPermission
from django.contrib import admin


@admin.register(Ticket)
class TicketChatAdmin(admin.ModelAdmin):
    change_form_template = 'websockets/model_changeform.html'
    list_display = (
        'category',
        'topic',
        'description',
        'status',
        'chat',
        'aceid',
        'unread_messages',
    )
    field_order = (
        'status',
    )
    fieldsets = (
        ('Ticket info', {
            'fields': (
                'category',
                'topic',
                'description',
                'status',
                'chat',
                'aceid',
            ),
        }),)

    def response_change(self, request, obj):
        if "_join_chat" in request.POST:
            chat = Chat.objects.filter(id=obj.chat_id).first()
            user = request.user
            chat.users.add(user)
            url = reverse_lazy("websockets:support_chat", kwargs=dict(chat_id=obj.chat_id))
            return redirect(url)

    def unread_messages(self, obj):
        if ChatPermission.objects.filter(chat_id=obj.chat_id, user_id=self.request.user.id):
            response = ChatPermission.objects.filter(chat_id=obj.chat_id, user_id=self.request.user.id).values_list('unread_messages', flat=True).first()
        else:
            response = "You are not in chat"
        return response

    def get_list_display(self, request):
        self.request = request
        return self.list_display
