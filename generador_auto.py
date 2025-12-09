#!/usr/bin/env python3
"""
Generador Automático de Links con Vista Previa
Incluye Auto-Deploy a GitHub → Netlify
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sys
import os
import subprocess
import json

class MetadataExtractor:
    """Extrae metadata para vista previa"""
    
    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    def __init__(self, url: str):
        self.url = url
    
    def extract(self):
        """Extrae título, descripción e imagen"""
        try:
            r = requests.get(self.url, headers=self.HEADERS, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Título
            title = None
            og_title = soup.find("meta", property="og:title")
            if og_title:
                title = og_title.get("content", "").strip()
            if not title and soup.title:
                title = soup.title.string.strip()
            if not title:
                title = "Sin título"
            
            # Descripción
            desc = None
            og_desc = soup.find("meta", property="og:description")
            if og_desc:
                desc = og_desc.get("content", "").strip()
            if not desc:
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc:
                    desc = meta_desc.get("content", "").strip()
            if not desc:
                desc = "Sin descripción"
            
            # Imagen
            img = ""
            og_img = soup.find("meta", property="og:image")
            if og_img:
                img = og_img.get("content", "").strip()
            if not img:
                first_img = soup.find("img")
                if first_img and first_img.get("src"):
                    img = urljoin(self.url, first_img["src"])
            
            return title, desc, img
            
        except Exception as e:
            raise Exception(f"Error extrayendo metadata: {e}")


def generate_html(visible_url, redirect_url, title, desc, img):
    """Genera HTML optimizado"""
    
    title = title.replace('"', '&quot;').replace("'", '&#39;')
    desc = desc.replace('"', '&quot;').replace("'", '&#39;')
    
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{desc}">
    
    <!-- Open Graph -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="{visible_url}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{desc}">
    <meta property="og:image" content="{img}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{desc}">
    <meta name="twitter:image" content="{img}">
    
    <!-- Redirección -->
    <meta http-equiv="refresh" content="0;url={redirect_url}">
    <script>window.location.href = "{redirect_url}";</script>
    
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .container {{
            text-align: center;
            padding: 2rem;
        }}
        .spinner {{
            border: 3px solid rgba(255,255,255,0.3);
            border-top: 3px solid white;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 1.5rem;
        }}
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        h1 {{
            font-size: 1.5rem;
            margin: 0 0 1rem;
            font-weight: 600;
        }}
        p {{
            opacity: 0.9;
            margin: 0.5rem 0;
        }}
        a {{
            color: white;
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="spinner"></div>
        <h1>Redirigiendo...</h1>
        <p>Serás redirigido automáticamente</p>
        <p><a href="{redirect_url}">O haz clic aquí</a></p>
    </div>
</body>
</html>"""


def check_git():
    """Verifica si Git está instalado"""
    try:
        subprocess.run(['git', '--version'], 
                      capture_output=True, 
                      check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def is_git_repo():
    """Verifica si estamos en un repositorio Git"""
    try:
        subprocess.run(['git', 'rev-parse', '--git-dir'],
                      capture_output=True,
                      check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def git_push_to_github(commit_message="Actualizar link preview"):
    """Hace commit y push a GitHub"""
    try:
        print("\n📤 Subiendo a GitHub...")
        
        # Añadir archivos
        subprocess.run(['git', 'add', 'index.html'], check=True)
        
        # Verificar si hay cambios
        result = subprocess.run(['git', 'status', '--porcelain'],
                              capture_output=True,
                              text=True,
                              check=True)
        
        if not result.stdout.strip():
            print("⚠️  No hay cambios para subir")
            return False
        
        # Commit
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        
        # Push
        subprocess.run(['git', 'push'], check=True)
        
        print("✅ Código subido a GitHub exitosamente")
        print("🚀 Netlify desplegará automáticamente en ~30 segundos")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error con Git: {e}")
        print("\n💡 Asegúrate de:")
        print("   1. Tener configurado Git: git config --global user.name 'Tu Nombre'")
        print("   2. Estar en un repo: git init")
        print("   3. Tener un remote: git remote add origin URL")
        return False


def setup_git_repo():
    """Ayuda a configurar un nuevo repositorio Git"""
    print("\n🔧 CONFIGURACIÓN DE REPOSITORIO GIT")
    print("="*60)
    
    # Inicializar repo
    try:
        subprocess.run(['git', 'init'], check=True)
        print("✅ Repositorio Git inicializado")
    except subprocess.CalledProcessError:
        print("❌ Error al inicializar Git")
        return False
    
    # Solicitar URL del repositorio
    print("\n📋 Necesitas crear un repositorio en GitHub:")
    print("   1. Ve a: https://github.com/new")
    print("   2. Crea un repositorio (por ejemplo: 'link-preview')")
    print("   3. Copia la URL del repositorio")
    
    repo_url = input("\n🔗 Pega la URL de tu repositorio GitHub: ").strip()
    
    if not repo_url:
        print("❌ URL requerida")
        return False
    
    try:
        # Añadir remote
        subprocess.run(['git', 'remote', 'add', 'origin', repo_url], check=True)
        
        # Configurar branch principal
        subprocess.run(['git', 'branch', '-M', 'main'], check=True)
        
        print("✅ Repositorio configurado correctamente")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        return False


def save_config(visible_url, redirect_url):
    """Guarda configuración para futuros usos"""
    config = {
        'last_visible_url': visible_url,
        'last_redirect_url': redirect_url
    }
    
    with open('.link_config.json', 'w') as f:
        json.dump(config, f, indent=2)


def load_config():
    """Carga configuración previa"""
    try:
        if os.path.exists('.link_config.json'):
            with open('.link_config.json', 'r') as f:
                return json.load(f)
    except:
        pass
    return None


def main():
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║     GENERADOR CON AUTO-DEPLOY GITHUB → NETLIFY           ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")
    
    # Verificar Git
    if not check_git():
        print("❌ Git no está instalado")
        print("📥 Descárgalo de: https://git-scm.com/downloads")
        sys.exit(1)
    
    # Cargar configuración previa
    config = load_config()
    if config:
        print("📋 Última configuración:")
        print(f"   Visible: {config.get('last_visible_url', 'N/A')}")
        print(f"   Oculto:  {config.get('last_redirect_url', 'N/A')}")
        usar_anterior = input("\n¿Usar estas URLs? (s/n): ").strip().lower()
        if usar_anterior == 's':
            visible = config['last_visible_url']
            hidden = config['last_redirect_url']
        else:
            visible = input("\n🔗 URL VISIBLE (para vista previa): ").strip()
            hidden = input("🎯 URL OCULTA (destino real): ").strip()
    else:
        visible = input("🔗 URL VISIBLE (para vista previa): ").strip()
        hidden = input("🎯 URL OCULTA (destino real): ").strip()
    
    if not visible or not hidden:
        print("\n❌ Necesitas ambas URLs")
        sys.exit(1)
    
    # Validación
    if not visible.startswith(('http://', 'https://')):
        print("❌ La URL visible debe empezar con http:// o https://")
        sys.exit(1)
    
    if not hidden.startswith(('http://', 'https://')):
        print("❌ La URL oculta debe empezar con http:// o https://")
        sys.exit(1)
    
    print("\n⏳ Extrayendo metadata...")
    
    try:
        # Extraer metadata
        extractor = MetadataExtractor(visible)
        title, desc, img = extractor.extract()
        
        print(f"\n✅ Metadata extraída:")
        print(f"   📝 Título: {title}")
        print(f"   📄 Descripción: {desc[:70]}...")
        print(f"   🖼️  Imagen: {'✓ Encontrada' if img else '✗ No encontrada'}")
        
        # Generar HTML
        html = generate_html(visible, hidden, title, desc, img)
        
        # Guardar HTML en el directorio actual
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"\n✅ Archivo generado: {os.path.abspath('index.html')}")
        
        # Guardar configuración
        save_config(visible, hidden)
        
        print("\n" + "="*65)
        print("RESUMEN:")
        print("="*65)
        print(f"Vista previa mostrará: {visible}")
        print(f"Click redirige a:      {hidden}")
        print("="*65)
        
        # Verificar si es repositorio Git
        if not is_git_repo():
            print("\n⚠️  No estás en un repositorio Git")
            configurar = input("¿Quieres configurar uno ahora? (s/n): ").strip().lower()
            
            if configurar == 's':
                if not setup_git_repo():
                    print("\n💡 Configura Git manualmente y vuelve a ejecutar el script")
                    sys.exit(0)
            else:
                print("\n💡 Para usar auto-deploy necesitas:")
                print("   1. git init")
                print("   2. git remote add origin TU_REPO_URL")
                sys.exit(0)
        
        # Preguntar si quiere hacer push
        print("\n🚀 OPCIONES DE DESPLIEGUE:")
        print("   1. Push automático a GitHub (Netlify desplegará solo)")
        print("   2. Solo generar archivo (push manual después)")
        
        opcion = input("\nElige una opción (1/2): ").strip()
        
        if opcion == "1":
            commit_msg = input("\n📝 Mensaje del commit (Enter para default): ").strip()
            if not commit_msg:
                commit_msg = f"Actualizar link preview: {title[:30]}"
            
            if git_push_to_github(commit_msg):
                print("\n🎉 ¡LISTO!")
                print("   → GitHub actualizado")
                print("   → Netlify desplegando...")
                print("   → Revisa tu sitio en ~30 segundos")
        else:
            print("\n✅ Archivo generado. Para subirlo manualmente ejecuta:")
            print("   git add index.html")
            print("   git commit -m 'Actualizar link'")
            print("   git push")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()