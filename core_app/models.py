import uuid
from django.db import models
from django.contrib.auth.models import User
from pytils.translit import slugify

class Category(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name='Изображение')
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=100,)

    def __str__(self):
        return self.name        


class Ad(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ads', verbose_name="Автор")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='ads', verbose_name="Категория")
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="Город")

    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.PositiveIntegerField(verbose_name="Цена (в тенге)", help_text="Укажите 0, если бесплатно")
    image = models.ImageField(upload_to='ads/', blank=True, null=True, verbose_name="Изображение")
    
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_moderated = models.BooleanField(default=False, verbose_name="Прошло модерацию")
    is_top = models.BooleanField(default=False, verbose_name="В топе")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Объявление"
        verbose_name_plural = "Объявления"
        # Автоматическая сортировка: сначала ТОП, потом самые свежие
        ordering = ['-is_top', '-created_at']    

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='favorited_by')
    image = models.ImageField(upload_to='categoties/', blank=True, null=True, verbose_name="Изображение")

    class Meta:
        unique_together = ('user', 'ad')


class Banner(models.Model):
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='banners/')
    link = models.URLField()
    is_active = models.BooleanField(default=True)
   
    def __str__(self):
        return f"{self.user.username} - {self.ad.title}"     

from django.core.validators import MinValueValidator, MaxValueValidator

class Review(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_written', verbose_name="Кто оставил")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received', verbose_name="На кого отзыв")
    
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Оценка"
    )
    text = models.TextField(verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        unique_together = ('author', 'recipient') 

    def __str__(self):
        return f"Отзыв от {self.author} для {self.recipient} ({self.rating}/5)"           