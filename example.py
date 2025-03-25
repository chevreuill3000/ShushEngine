from shush.motor import Motor
import time

m = None  # Important : pour que le bloc finally sache si m est défini

try:
    # Initialise le moteur m0
    m = Motor(0)

    # Active le moteur
    print("🟢 Activation du moteur")
    m.enable_motor()

    # Envoie à une position arbitraire
    print("➡️ Déplacement à +100000")
    m.go_to(100000)

    # Attendre que le moteur atteigne la position
    time.sleep(2)

    # Lire la position
    pos = m.get_position()
    print(f"📍 Position actuelle : {pos}")

    # Stoppe le moteur
    print("🛑 Arrêt du moteur")
    m.stop_motor()

except KeyboardInterrupt:
    print("\n⚠️ Interruption clavier. Arrêt du moteur...")

except Exception as e:
    print(f"❌ Erreur : {e}")

finally:
    if m:
        print("♻️ Libération des ressources")
        m.deinitBoard()
        print("✅ Terminé")
    else:
        print("⚠️ Aucune ressource à libérer (le moteur n'a pas été initialisé)")
