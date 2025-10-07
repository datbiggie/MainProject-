# Script para copiar los estilos de chatbot de registrar_persona a registrar_empresa

# Leer los estilos de registrar_persona (desde línea 962 en adelante)
with open(r'c:\GitHub\MainProject-\ecommerce_app\static\registrar_persona\css\main.css', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Extraer solo las líneas de estilos de chatbot (líneas 962+)
chatbot_styles = ''.join(lines[961:])  # Desde línea 962 (índice 961)

# Leer el archivo de registrar_empresa
with open(r'c:\GitHub\MainProject-\ecommerce_app\static\registrar_empresa\css\main.css', 'r', encoding='utf-8') as f:
    empresa_content = f.read()

# Verificar si los estilos ya están
if 'chatbot-customization-section' not in empresa_content:
    # Agregar los estilos al final
    with open(r'c:\GitHub\MainProject-\ecommerce_app\static\registrar_empresa\css\main.css', 'a', encoding='utf-8') as f:
        f.write('\n\n')
        f.write(chatbot_styles)
    print("✓ Estilos CSS de chatbot copiados exitosamente a registrar_empresa")
else:
    print("✓ Los estilos CSS de chatbot ya existen en registrar_empresa")
