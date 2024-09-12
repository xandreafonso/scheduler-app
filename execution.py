import subprocess

def install_dependencies(dependencies):
    if dependencies:
        try:
            subprocess.run(['pip', 'install'] + dependencies.split(), check=True)
        except subprocess.CalledProcessError as e:
            print(f"Erro ao instalar dependências: {e}")

def execute_script(script_content, dependencies=None):
    try:
        if dependencies:
            install_dependencies(dependencies)

        exec(script_content)
    except Exception as e:
        print(f"Erro ao executar o script: {e}")