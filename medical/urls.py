from django.urls import path
from . import views
from django.urls import path
from . import views

urlpatterns = [
    # This maps the root URL (e.g., http://127.0.0) to your home view
    path('', views.home, name='home'),
]

urlpatterns = [
    path("", views.index, name="index"),
    path("case/new/", views.new_case, name="new_case"),
    path("case/<int:case_id>/", views.case_detail, name="case_detail"),
    path("case/<int:case_id>/analyze/", views.analyze_case, name="analyze_case"),
    path("case/<int:case_id>/report/", views.report_view, name="report_view"),
    path("history/", views.history, name="history"),
]
