from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from rest_framework import serializers

from reviews.models import Category, Comment, Genre, Review, Title, User


class TokenSerializer(serializers.Serializer):
    username = serializers.CharField(validators=[UnicodeUsernameValidator])
    confirmation_code = serializers.CharField()

    class Meta:
        fields = ("username", "confirmation_code")


class SignUpSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    username = serializers.CharField(
        required=True, validators=[UnicodeUsernameValidator]
    )

    def validate(self, data):
        if data["username"] == "me":
            raise ValidationError("Пользователь не может иметь имя 'me'")
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "bio",
            "role",
        )


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("name", "slug")


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("name", "slug")


class WriteTitleSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Category.objects.all(),
    )
    genre = serializers.SlugRelatedField(
        many=True,
        slug_field="slug",
        queryset=Genre.objects.all(),
    )
    rating = serializers.IntegerField(read_only=True, initial=0)

    class Meta:
        model = Title
        fields = "__all__"


class ReadTitleSerializer(serializers.ModelSerializer):
    genre = GenreSerializer(many=True)
    category = CategorySerializer()
    rating = serializers.IntegerField(read_only=True, initial=0)

    class Meta:
        model = Title
        fields = "__all__"
        read_only_fields = ("name", "year", "description", "genre", "category")


class ReviewSerializer(serializers.ModelSerializer):
    score = serializers.IntegerField(max_value=10, min_value=1)
    author = serializers.SlugRelatedField(
        slug_field="username",
        read_only=True,
    )

    class Meta:
        model = Review
        fields = ("id", "text", "author", "score", "pub_date")

    def validate(self, data):
        if not self.context["request"].method == "POST":
            return data
        if Review.objects.filter(
            title_id=self.context["view"].kwargs.get("title_id"),
            author=self.context["request"].user,
        ).exists():
            raise serializers.ValidationError(
                (
                    "Автор может оставлять ревью на каждое произведение "
                    "только один раз"
                )
            )
        return data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field="username",
        read_only=True,
    )

    class Meta:
        model = Comment
        fields = ("id", "text", "author", "pub_date")
