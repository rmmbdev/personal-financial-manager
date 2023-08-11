from django.urls import path

from .views import *

urlpatterns = [
    path('', HomePageView.as_view(), name='homepage'),
    path('add-tag/', AddTagView.as_view(), name='add_tag'),
    path('edit-tag/', EditsTagView.as_view(), name='edit_tag'),
    path('remove-tag/', RemoveTagView.as_view(), name='remove_tag'),
    path('add-transaction/', AddTransactionView.as_view(), name='add_transaction'),
    path('edit-transaction/', EditTransactionView.as_view(), name='edit_transaction'),
    path('remove-transaction/', remove_transaction, name='remove_transaction'),

]
