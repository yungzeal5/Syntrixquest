from django.urls import path

from .views import OperationsOverviewView

urlpatterns = [
    path("overview/", OperationsOverviewView.as_view(), name="operations-overview"),
]
