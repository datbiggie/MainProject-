# Script para agregar debug temporal al JavaScript
import os

js_file_path = r"c:\GitHub\MainProject-\ecommerce_app\static\producto_sucursal\js\producto_config.js"

print("=== Agregando debug temporal al JavaScript ===")

# Leer el archivo actual
with open(js_file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar la línea donde se determina el userType
lines = content.split('\n')
new_lines = []

for i, line in enumerate(lines):
    new_lines.append(line)
    
    # Agregar debug después de la línea que obtiene userType
    if 'const userType = userTypeElement?.getAttribute' in line:
        new_lines.append('                ')
        new_lines.append('                // ===== DEBUG ADICIONAL =====')
        new_lines.append('                console.log("🔍 BUTTON:", button);')
        new_lines.append('                console.log("🔍 BUTTON.closest(.container):", button.closest(".container"));')
        new_lines.append('                console.log("🔍 TODOS LOS ELEMENTOS CON data-user-type:", document.querySelectorAll("[data-user-type]"));')
        new_lines.append('                const allContainers = document.querySelectorAll(".container");')
        new_lines.append('                console.log("🔍 TODOS LOS CONTENEDORES .container:", allContainers);')
        new_lines.append('                allContainers.forEach((container, index) => {')
        new_lines.append('                    const userTypeAttr = container.getAttribute("data-user-type");')
        new_lines.append('                    console.log(`🔍 Container ${index}: data-user-type = "${userTypeAttr}"`);')
        new_lines.append('                });')
        new_lines.append('                console.log("🔍 userTypeElement FINAL:", userTypeElement);')
        new_lines.append('                if (userTypeElement) {')
        new_lines.append('                    console.log("🔍 userTypeElement.tagName:", userTypeElement.tagName);')
        new_lines.append('                    console.log("🔍 userTypeElement.className:", userTypeElement.className);')
        new_lines.append('                    console.log("🔍 userTypeElement.getAttribute(\"data-user-type\"):", userTypeElement.getAttribute("data-user-type"));')
        new_lines.append('                } else {')
        new_lines.append('                    console.log("❌ userTypeElement es null o undefined");')
        new_lines.append('                }')
        new_lines.append('                // ===== FIN DEBUG ADICIONAL =====')
        new_lines.append('                ')

# Escribir el archivo modificado
with open(js_file_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print("✅ Debug agregado al archivo JavaScript")
print("\nAhora:")
print("1. Recarga la página en el navegador")
print("2. Abre DevTools (F12)")
print("3. Ve a la pestaña Console")
print("4. Haz clic en el botón 'Editar' de un producto")
print("5. Revisa los logs que empiecen con 🔍")
print("\nEsto nos ayudará a identificar exactamente por qué no se detecta el userType correctamente.")