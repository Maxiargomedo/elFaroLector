from django.urls import path
from . import views
from .views import mantenedor_promociones 

urlpatterns = [
    path('', views.lector_precios, name='home'),
    path('lector_precios/', views.lector_precios, name='lector_precios'),
    path('buscar_producto/', views.buscar_producto, name='buscar_producto'),
    path('mantenedor_promociones/', mantenedor_promociones, name='mantenedor_promociones'),
    path('lista_productos/', views.lista_productos, name='lista_productos'),
    path('editar_producto/<int:producto_id>/', views.editar_producto, name='editar_producto'),
    path('eliminar_producto/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    path('agregar_producto/', views.agregar_producto, name='agregar_producto'),
    path('importar-exportar-precios/', views.import_export_precios, name='import_export_precios'),
    path('export-productos-csv/', views.export_productos_csv, name='export_productos_csv'),
    # URLs de prueba y debug
    path('test-email/', views.test_email, name='test_email'),
    path('test-busqueda/', views.test_busqueda_internet, name='test_busqueda'),
    path('test-correo/', views.test_correo_completo, name='test_correo'),
    path('test-correo-google/', views.test_correo_con_google, name='test_correo_google'),
    # En la lista urlpatterns, agregar estas nuevas URLs:
    path('test-google-simple/', views.test_google_simple, name='test_google_simple'),
    path('buscar_producto_barcode/', views.buscar_producto_barcode, name='buscar_producto_barcode'),
    path('api/imagenes_promociones/', views.api_imagenes_promociones, name='api_imagenes_promociones'),
    path('api/imagenes_promociones/', views.imagenes_promociones, name='imagenes_promociones'),
    path('verificar_conexion/', views.verificar_conexion, name='verificar_conexion'),



    #path('test-selenium/', views.test_scraper_selenium, name='test_selenium'),
    #path('debug-jumbo/', views.debug_jumbo_html, name='debug_jumbo'),
    #path('analizar-html/', views.analizar_html_capturado, name='analizar_html'),
    #path('test-codigos/', views.test_codigos_reales_jumbo, name='test_codigos'),
    #path('test-populares/', views.test_productos_populares_jumbo, name='test_populares'),  
    #path('test-url-directa/', views.test_url_directa_jumbo, name='test_url_directa'),      
]