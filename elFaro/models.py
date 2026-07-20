from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation

def validate_price_value(value):
    """Validador personalizado para precios"""
    if value is None:
        return
    
    # Verificar que el valor no sea demasiado grande
    if value > 9999999:
        raise ValidationError(f'El precio {value} es demasiado grande. Máximo permitido: 9,999,999')
    
    # Verificar que el valor sea positivo
    if value < 0:
        raise ValidationError(f'El precio {value} debe ser positivo')
    
    # Verificar que sea un entero (sin decimales)
    try:
        if value != int(value):
            raise ValidationError(f'El precio {value} debe ser un número entero sin decimales')
    except (ValueError, OverflowError):
        raise ValidationError(f'El precio {value} no es un valor válido')

class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, blank=True, null=True)
    codigo_barras = models.CharField(max_length=30, unique=True)  # Debe ser CharField
    precio = models.DecimalField(max_digits=7, decimal_places=0, validators=[validate_price_value])
    precio_vecino = models.DecimalField(max_digits=7, decimal_places=0, blank=True, null=True, validators=[validate_price_value])
    imagen_url = models.CharField(max_length=500, blank=True, null=True)
    
    def clean(self):
        """Validación adicional a nivel de modelo"""
        super().clean()
        
        # Validar precio
        if self.precio is not None:
            try:
                validate_price_value(self.precio)
            except ValidationError as e:
                raise ValidationError({'precio': e.message})
        
        # Validar precio_vecino
        if self.precio_vecino is not None:
            try:
                validate_price_value(self.precio_vecino)
            except ValidationError as e:
                raise ValidationError({'precio_vecino': e.message})

    def save(self, *args, **kwargs):
        """Override save para asegurar validación antes de guardar"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.codigo_barras})"


class ImagenPromocion(models.Model):
    imagen = models.ImageField(upload_to='promociones/')
    nombre = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.nombre or f"Promoción {self.id}"

from django import forms
from .models import Producto

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = '__all__'

    def clean_codigo_barras(self):
        codigo = self.cleaned_data['codigo_barras']
        return codigo.strip()