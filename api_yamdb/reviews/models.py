import random
import string

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


def rand_slug():
    return "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(6)
    )


class UserRole:
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


ROLE_CHOICES = (
    (UserRole.ADMIN, "Администратор"),
    (UserRole.USER, "Пользователь"),
    (UserRole.MODERATOR, "Модератор"),
)


class User(AbstractUser):
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        verbose_name="имя пользователя",
        max_length=150,
        unique=True,
        help_text="Необходимые. 150 символов или меньше.",
        validators=[username_validator],
        error_messages={
            "unique": "Пользователь с таким именем уже существует.",
        },
    )
    first_name = models.CharField(
        verbose_name="имя",
        max_length=150,
        blank=True,
    )
    last_name = models.CharField(
        verbose_name="фамилия",
        max_length=150,
        blank=True,
    )
    email = models.EmailField(
        verbose_name="адрес электронной почты",
        blank=False,
        unique=True,
        max_length=254,
        error_messages={
            "unique": ("Электронная почта занята."),
        },
    )
    bio = models.TextField(verbose_name="опишите себя", blank=True)
    is_active = models.BooleanField(default=True)
    role = models.CharField(
        verbose_name="роль",
        max_length=60,
        choices=ROLE_CHOICES,
        null=False,
        default=UserRole.USER,
    )

    REQUIRED_FIELDS = ["email"]

    def save(self, *args, **kwargs):
        if self.username == "me":
            return ValidationError("Username не может быть 'me'.")
        else:
            super().save(*args, **kwargs)

    @property
    def is_moderator(self):
        return self.role == UserRole.MODERATOR

    @property
    def is_admin(self):
        return self.is_superuser or self.role == UserRole.ADMIN

    @property
    def is_user(self):
        return self.role == UserRole.USER

    def get_full_name(self) -> str:
        return self.username

    def get_short_name(self) -> str:
        return self.username[:15]

    def __str__(self):
        return f"{self.username} is a {self.role}"

    class Meta:

        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"
        constraints = [
            models.CheckConstraint(
                check=~models.Q(username="me"),
                name="Пользователь не может быть назван me!",
            )
        ]


class Category(models.Model):
    name = models.CharField(
        verbose_name="название",
        max_length=256,
        unique=True,
    )
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(rand_slug + "-" + self.name[:15])
        super().save(*args, **kwargs)


class Genre(models.Model):
    name = models.CharField(
        verbose_name="название жанра",
        max_length=256,
        unique=True,
    )
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "жанр"
        verbose_name_plural = "жанры"

    def __str__(self):
        return self.name[:15]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(rand_slug + "-" + self.name[:15])
        super().save(*args, **kwargs)


class Title(models.Model):
    name = models.CharField(
        verbose_name="название произведения",
        max_length=256,
    )
    year = models.PositiveSmallIntegerField(
        verbose_name="год выпуска произведения",
        blank=True,
        validators=[
            MinValueValidator(0, "Год произведения должен быть больше 0."),
            MaxValueValidator(
                timezone.now().year,
                "Год произведения должен быть меньше текущего.",
            ),
        ],
    )
    description = models.TextField(
        verbose_name="описание произведения",
        max_length=300,
        default="нет описания",
    )
    genre = models.ManyToManyField(
        Genre,
        verbose_name="жанр произведения",
        through="GenreTitle",
        help_text="Выберете жанр",
    )
    category = models.ForeignKey(
        Category,
        verbose_name="категория произведения",
        on_delete=models.SET_NULL,
        related_name="titles",
        null=True,
        help_text="Выберете категорию",
    )

    class Meta:
        verbose_name = "произведение"
        verbose_name_plural = "произведения"

    def __str__(self):
        return self.name[:15]


class GenreTitle(models.Model):
    """Through this model Genre and Title models ale linked."""

    title = models.ForeignKey(Title, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True)


class Review(models.Model):
    text = models.TextField(verbose_name="текст отзыва")
    title = models.ForeignKey(
        Title,
        related_name="reviews",
        on_delete=models.CASCADE,
        verbose_name="произведение для отзыва",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="автор отзыва",
    )
    score = models.PositiveIntegerField(
        verbose_name="оценка произведения",
        validators=[
            MinValueValidator(1, "Минимальная оценка - 1."),
            MaxValueValidator(10, "Максимальная оценка - 10"),
        ],
    )
    pub_date = models.DateTimeField(
        auto_now_add=True, verbose_name="дата публикации", db_index=True
    )

    class Meta:
        ordering = (
            "title",
            "-pub_date",
        )
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        constraints = [
            models.UniqueConstraint(
                fields=("author", "title"),
                name="author_title_only_on_review",
            )
        ]

    def __str__(self):
        return f"{self.author.username[:15]}, {self.text[:15]}, {self.score}"


class Comment(models.Model):
    text = models.TextField(verbose_name="текст комментария")
    review = models.ForeignKey(
        Review,
        related_name="comments",
        on_delete=models.CASCADE,
        verbose_name="отзыв для комментария",
    )
    author = models.ForeignKey(
        User,
        related_name="comments",
        on_delete=models.CASCADE,
        verbose_name="автор комментария",
    )
    pub_date = models.DateTimeField(
        verbose_name="дата публикации", auto_now_add=True, db_index=True
    )

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self):
        return self.text
