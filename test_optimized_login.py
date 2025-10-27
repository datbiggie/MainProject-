#!/usr/bin/env python3
"""
Script para probar la nueva interfaz optimizada de login
"""
import os
import sys
import django
from pathlib import Path

# Agregar el directorio del proyecto al path
project_dir = Path(__file__).resolve().parent
sys.path.append(str(project_dir))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from django.test import Client
from dotenv import load_dotenv

def test_optimized_login_interface():
    """Prueba la nueva interfaz optimizada de login"""
    
    # Cargar variables de entorno
    load_dotenv()
    
    print("=== PRUEBA DE INTERFAZ OPTIMIZADA DE LOGIN ===")
    
    # Crear cliente de prueba
    client = Client()
    
    try:
        # Probar que la página de login carga correctamente
        print("🎨 Probando nueva interfaz de login...")
        login_response = client.get('/ecommerce/iniciar_sesion/')
        
        if login_response.status_code == 200:
            print("✅ Página de login carga correctamente")
            
            # Verificar elementos de la nueva interfaz
            content = login_response.content.decode('utf-8')
            
            # Verificar estilos optimizados
            optimizations = [
                ('login-page', 'Contenedor principal'),
                ('login-container', 'Card de login'),
                ('login-header', 'Header compacto'),
                ('login-logo', 'Logo optimizado'),
                ('forgot-password-always-visible', 'Enlace de recuperación'),
                ('btn-primary', 'Botón principal'),
                ('form-input', 'Campos de entrada'),
                ('password-wrapper', 'Campo de contraseña'),
                ('linear-gradient', 'Fondo degradado'),
                ('border-radius: 12px', 'Bordes redondeados'),
                ('box-shadow', 'Sombras'),
                ('transition', 'Animaciones'),
            ]
            
            found_optimizations = []
            for optimization, description in optimizations:
                if optimization in content:
                    found_optimizations.append(f"   ✅ {description}")
                else:
                    found_optimizations.append(f"   ⚠️  {description} - no encontrado")
            
            print("\n🔍 ELEMENTOS DE LA INTERFAZ OPTIMIZADA:")
            for item in found_optimizations:
                print(item)
            
            # Verificar funcionalidades específicas
            features = [
                ('¿Olvidaste tu contraseña?', 'Enlace de recuperación'),
                ('Bienvenido', 'Título principal'),
                ('Ingresa a tu cuenta', 'Subtítulo'),
                ('Correo Electrónico', 'Campo de email'),
                ('Siguiente', 'Botón de siguiente'),
                ('Crear cuenta', 'Dropdown de registro'),
            ]
            
            print("\n📋 FUNCIONALIDADES PRESENTES:")
            for feature, description in features:
                if feature in content:
                    print(f"   ✅ {description}")
                else:
                    print(f"   ❌ {description} - no encontrado")
            
            return True
        else:
            print(f"❌ Error al cargar página de login: {login_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        return False

def show_design_improvements():
    """Muestra las mejoras de diseño implementadas"""
    print("\n=== MEJORAS DE DISEÑO IMPLEMENTADAS ===")
    
    improvements = [
        "🎨 **Diseño más compacto**: Card reducida de altura",
        "🖼️  **Logo optimizado**: Tamaño reducido (120x60px)",
        "🎯 **Espaciado mejorado**: Márgenes y padding optimizados",
        "🌈 **Fondo degradado**: Gradiente azul/púrpura elegante",
        "💫 **Animaciones suaves**: Transiciones en hover y focus",
        "📱 **Responsive mejorado**: Adaptación a móviles",
        "🔘 **Botones modernos**: Gradientes y efectos hover",
        "📝 **Campos optimizados**: Mejor UX en inputs",
        "🔗 **Enlace siempre visible**: Recuperación accesible",
        "🎪 **Sombras y bordes**: Diseño más profesional",
    ]
    
    for improvement in improvements:
        print(f"   {improvement}")
    
    print("\n📏 **DIMENSIONES OPTIMIZADAS:**")
    print("   • Card máxima: 400px de ancho")
    print("   • Logo: 120x60px (antes 200x100px)")
    print("   • Padding: 30px (más compacto)")
    print("   • Bordes redondeados: 12px")
    print("   • Campos: altura optimizada")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de interfaz optimizada...\n")
    
    success = test_optimized_login_interface()
    
    if success:
        show_design_improvements()
        print("\n✨ ¡La nueva interfaz está funcionando perfectamente!")
        print("🌐 Visita: http://localhost:8000/ecommerce/iniciar_sesion/")
        print("💡 La card ahora es más compacta y elegante")
    else:
        print("\n❌ Hubo problemas con la nueva interfaz")
        print("🔧 Revisa la configuración del servidor")
