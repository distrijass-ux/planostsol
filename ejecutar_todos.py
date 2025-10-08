"""
Script para ejecutar la generación TSOL de ambas empresas
DISTRIJASS CALI (211688) y EJE CAFETERO (211697)
"""
import subprocess
import sys

def ejecutar_script(nombre_script, descripcion):
    """Ejecuta un script Python y muestra el resultado"""
    print(f"\n{'='*80}")
    print(f"Ejecutando: {descripcion}")
    print(f"{'='*80}\n")
    
    try:
        resultado = subprocess.run(
            [sys.executable, nombre_script],
            capture_output=False,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error al ejecutar {nombre_script}")
        print(f"Código de salida: {e.returncode}")
        return False
    except Exception as e:
        print(f"\n✗ Error inesperado: {e}")
        return False

if __name__ == '__main__':
    print("\n" + "="*80)
    print("=== GENERADOR TSOL - DISTRIJASS (AMBAS EMPRESAS) ===")
    print("="*80)
    
    resultados = {}
    
    # Ejecutar Distrijass Cali
    print("\n[1/2] Procesando DISTRIJASS CALI...")
    resultados['Distrijass Cali'] = ejecutar_script('PlanosTsol_Distrijass.py', 'DISTRIJASS CALI (211688)')
    
    # Ejecutar Eje Cafetero
    print("\n[2/2] Procesando DISTRIJASS EJE CAFETERO...")
    resultados['Eje Cafetero'] = ejecutar_script('PlanosTsol_Eje.py', 'DISTRIJASS EJE CAFETERO (211697)')
    
    # Resumen final
    print("\n" + "="*80)
    print("=== RESUMEN DE EJECUCIÓN ===")
    print("="*80)
    
    exitosos = 0
    fallidos = 0
    
    for empresa, exito in resultados.items():
        if exito:
            print(f"✓ {empresa}: EXITOSO")
            exitosos += 1
        else:
            print(f"✗ {empresa}: FALLIDO")
            fallidos += 1
    
    print(f"\nTotal: {exitosos} exitosos, {fallidos} fallidos")
    print("\nProcesamiento completado.\n")
    
    # Salir con código de error si hubo fallos
    sys.exit(0 if fallidos == 0 else 1)
