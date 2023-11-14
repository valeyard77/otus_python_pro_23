from django.urls import path

from .views import (
    IndexView, SearchView, QuestionView, JsonQuestionVote, JsonAnswerVote, JsonAnswerMark, ask
)

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('question/<str:slug>,<int:pk>/', QuestionView.as_view(), name='question'),
    path('question/<int:pk>/vote/', JsonQuestionVote.as_view(), name='question_vote'),
    path('answer/<int:pk>/vote/', JsonAnswerVote.as_view(), name='answer_vote'),
    path('answer/<int:pk>/mark/', JsonAnswerMark.as_view(), name='answer_mark'),
    path('ask/', ask, name='ask'),
    path('search/', SearchView.as_view(), name='search'),
]
