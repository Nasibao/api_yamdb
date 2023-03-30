from django.contrib.auth.tokens import default_token_generator
from django.db import IntegrityError
from django.db.models import Avg, ExpressionWrapper, fields
from django.shortcuts import get_object_or_404
from rest_framework import (
    filters,
    generics,
    mixins,
    pagination,
    permissions,
    response,
    status,
    viewsets,
)
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework_simplejwt.tokens import AccessToken

from reviews.models import Category, Genre, Review, Title, User

from .filters import TitleFilter
from .permissions import (
    IsAdmin,
    IsAdminOrReadOnly,
    OwnerAdminModeratorOrReadOnly,
)
from .serializers import (
    CategorySerializer,
    CommentSerializer,
    GenreSerializer,
    ReadTitleSerializer,
    ReviewSerializer,
    SignUpSerializer,
    TokenSerializer,
    UserSerializer,
    WriteTitleSerializer,
)


@api_view(["POST"])
def token(request):
    serializer = TokenSerializer(data=request.data)
    if serializer.is_valid():
        user = get_object_or_404(User, username=request.data["username"])
        confirmation_code = request.data["confirmation_code"]
        if default_token_generator.check_token(user, confirmation_code):
            token = AccessToken.for_user(user)
            response = {
                "username": request.data["username"],
                "token": str(token),
            }
            return Response(response, status=status.HTTP_200_OK)
        raise ValidationError(detail="Неверный код подтверждения.")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def signup(request):
    serializer = SignUpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        user = User.objects.get_or_create(
            username=serializer.validated_data["username"],
            email=serializer.validated_data["email"],
        )[0]
    except IntegrityError as e:
        return Response(data=repr(e), status=status.HTTP_400_BAD_REQUEST)
    confirmation_code = default_token_generator.make_token(user)
    user.email_user(
        subject="Сonfirmation code",
        message=f"Yamdb. Код подтверждения -  {confirmation_code}",
        from_email="administration@yamdb.com",
    )
    return Response(serializer.data, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    lookup_field = "username"
    filter_backends = (filters.SearchFilter,)
    search_fields = ("username",)
    pagination_class = pagination.LimitOffsetPagination

    @action(
        detail=False,
        methods=["GET", "PATCH"],
        url_path="me",
        permission_classes=[permissions.IsAuthenticated],
    )
    def get_self_user_page(self, request):
        if request.method == "GET":
            serializer = UserSerializer(request.user)
            return response.Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(role=request.user.role, partial=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class CustomizedListCreateDestroyViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    filter_backends = (filters.OrderingFilter, filters.SearchFilter)
    ordering_fields = ("name",)
    search_fields = ("name",)
    lookup_field = "slug"
    pagination_class = pagination.LimitOffsetPagination
    permission_classes = [IsAdminOrReadOnly]


class CategoryViewSet(CustomizedListCreateDestroyViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(CustomizedListCreateDestroyViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.prefetch_related("reviews").annotate(
        rating=ExpressionWrapper(
            Avg("reviews__score"),
            output_field=fields.IntegerField(),
        )
    )
    ordering_fields = ("name",)
    filterset_class = TitleFilter
    pagination_class = pagination.LimitOffsetPagination
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action == "retrieve" or self.action == "list":
            return ReadTitleSerializer
        return WriteTitleSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    pagination_class = pagination.LimitOffsetPagination
    permission_classes = (OwnerAdminModeratorOrReadOnly,)

    def get_queryset(self):
        title = generics.get_object_or_404(
            Title,
            id=self.kwargs.get("title_id"),
        )
        return title.reviews.select_related("author").all()

    def perform_create(self, serializer):
        title_id = self.kwargs.get("title_id")
        title = generics.get_object_or_404(Title, id=title_id)
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    pagination_class = pagination.LimitOffsetPagination
    permission_classes = (OwnerAdminModeratorOrReadOnly,)

    def get_queryset(self):
        review = generics.get_object_or_404(
            Review,
            id=self.kwargs.get("review_id"),
        )
        return review.comments.select_related("author").all()

    def perform_create(self, serializer):
        review_id = self.kwargs.get("review_id")
        review = generics.get_object_or_404(Review, id=review_id)
        serializer.save(author=self.request.user, review=review)
