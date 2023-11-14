from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    IndexAPIView, TrendingAPIView, SearchAPIView, AnswersAPIView,
    LoginAPIView, QuestionVoteAPIView, AnswerVoteAPIView,
)

urlpatterns = [
    path("", view=IndexAPIView.as_view(), name="questions"),
    path("trending/", view=TrendingAPIView.as_view(), name="trending"),
    path('search/', view=SearchAPIView.as_view(), name="search"),
    path("questions/<int:pk>/answers/", view=AnswersAPIView.as_view(), name="answers"),
    path("questions/<int:pk>/vote/", view=QuestionVoteAPIView.as_view(), name="question_vote"),
    path("answers/<int:pk>/vote/", view=AnswerVoteAPIView.as_view(), name="answer_vote"),
    path("login/", view=LoginAPIView.as_view(), name="login"),
]

urlpatterns = format_suffix_patterns(urlpatterns)
