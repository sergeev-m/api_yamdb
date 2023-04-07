from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import mixins, viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action, api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.db.models import Avg

from reviews.models import Category, Genre, Title, User, Review
from .serializers import (CategoriesSerializer, GenreSerializer,
                          TitlesWriteSerializer, TitlesReadSerializer,
                          SignUpSerializer, UserSerializer, ProfileSerializer,
                          ReviewSerializer, CommentSerializer)

from .filters import TitlesFilter, UserFilter
from .permissions import IsAdmin, IsOwnerModerAdminOrReadOnly, RolePermissions
from .utils import send_token


class WithoutPatchPutViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                             mixins.DestroyModelMixin,
                             viewsets.GenericViewSet):
    pass


class CategoriesViewSet(WithoutPatchPutViewSet):
    """Категории"""
    queryset = Category.objects.all()
    serializer_class = CategoriesSerializer
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class GenreViewSet(WithoutPatchPutViewSet):
    """Жанры"""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class TitlesViewSet(viewsets.ModelViewSet):
    """Произведения"""
    queryset = Title.objects.all().annotate(
        Avg('reviews__score'))
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitlesFilter

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return TitlesWriteSerializer
        return TitlesReadSerializer


@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    """Регистрация и авторизация"""
    serializer = SignUpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user, _ = User.objects.get_or_create(**serializer.validated_data)
    send_token(user)
    return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """Пользователи"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'
    filter_backends = [DjangoFilterBackend, ]
    filterset_class = UserFilter
    permission_classes = [IsAdmin, ]
    http_method_names = ['get', 'post', 'patch', 'delete']

    @action(methods=['patch', 'get'], detail=False,
            permission_classes=[RolePermissions],
            url_path='me', url_name='me',
            serializer_class=ProfileSerializer)
    def me(self, request, *args, **kwargs):
        """Профиль пользователя"""
        user = self.request.user
        serializer = self.get_serializer(user)
        if self.request.method == 'PATCH':
            serializer = self.get_serializer(
                user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReviewVieSet(viewsets.ModelViewSet):
    """Отзывы"""
    serializer_class = ReviewSerializer
    permission_classes = [IsOwnerModerAdminOrReadOnly]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_title(self):
        return get_object_or_404(Title, id=self.kwargs.get('title_id'))

    def get_queryset(self):
        return self.get_title().reviews.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, title=self.get_title())


class CommentViewSet(viewsets.ModelViewSet):
    """Комментарии к отзывам"""
    serializer_class = CommentSerializer
    permission_classes = [IsOwnerModerAdminOrReadOnly]

    def get_review(self):
        return get_object_or_404(Review, id=self.kwargs.get('review_id'))

    def get_queryset(self):
        return self.get_review().comments.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, review=self.get_review())
