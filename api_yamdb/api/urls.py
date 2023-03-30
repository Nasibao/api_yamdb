from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from api.views import (
    CategoryViewSet,
    CommentViewSet,
    GenreViewSet,
    ReviewViewSet,
    TitleViewSet,
    UserViewSet,
    signup,
    token,
)

v1_router = DefaultRouter()

v1_router.register(r"users", UserViewSet, basename="users")
v1_router.register(r"categories", CategoryViewSet, basename="categories")
v1_router.register(r"genres", GenreViewSet, basename="genres")
v1_router.register(r"titles", TitleViewSet, basename="titles")
v1_router.register(
    r"^titles/(?P<title_id>\d+)/reviews",
    ReviewViewSet,
    basename="reviews",
)
v1_router.register(
    r"^titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments",
    CommentViewSet,
    basename="comments",
)

authpatterns = [
    path("token/", token, name="token_obtain"),
    path("signup/", signup, name="auth_signup"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

urlpatterns = [
    path("v1/", include(v1_router.urls)),
    path("v1/auth/", include(authpatterns)),
]
