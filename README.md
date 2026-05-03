# 🎮 Psykanoid

Ein modernes 2-Spieler Breakout Spiel für Windows.

## 📖 Beschreibung

Psykanoid ist ein Breakout Spiel mit Singleplayer und 2-Spieler Modus. Zwei Spieler können gleichzeitig auf demselben Bildschirm spielen und um Punkte konkurrieren.

## ✨ Features

- 🎯 **Singleplayer oder 2-Spieler Modus** - Wähle deinen Spielstil am Startbildschirm
- 🎱 Zwei Bälle für einen kompetitiven Punkte-Wettkampf
- 🧱 Level mit buntem Grid aus Steinen (einige benötigen 2 Treffer mit Farbwechsel)
- 📐 Präzise Kollisionserkennung mit dynamischem Abprallwinkel am Paddle
- 🔊 Synthetische Sound-Effekte (keine externen Dateien benötigt)

## 🎮 Steuerung

### Singleplayer Modus
| Spieler | Tasten |
|---------|--------|
| **Spieler 1** | `A` (links), `D` (rechts) |

### 2-Spieler Modus
| Spieler | Tasten |
|---------|--------|
| **Spieler 1** | `A` (links), `D` (rechts) |
| **Spieler 2** | `←` (links), `→` (rechts) |

| **Beide** | `ESC` (beenden), `LEERTASTE` (neu starten nach Game Over) |

## 🛠️ Systemanforderungen

- Windows 10/11
- Python 3.12+
- 27 MB Speicherplatz für die exe

## 📦 Installation

### Option 1: Direkt aus der exe (Empfohlen)

Laden Sie die fertige `Psykanoid.exe` herunter und starten Sie sie direkt. Keine Installation erforderlich!

### Option 2: Von Quellcode aus

```bash
# 1. Python 3.12 installieren (falls nicht vorhanden)
# Download: https://www.python.org/downloads/

# 2. Projekt-Verzeichnis öffnen
cd c:/LAB/Psykanoid

# 3. Virtuelle Umgebung erstellen
"C:\Users\Sebas\AppData\Local\Programs\Python\Python312\python.exe" -m venv .venv

# 4. Abhängigkeiten installieren
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install pygame numpy pyinstaller

# 5. Spiel ausführen
.venv\Scripts\python.exe psykanoid.py

# 6. Oder zur standalone exe kompilieren
.venv\Scripts\python.exe -m PyInstaller --onefile --windowed --name Psykanoid psykanoid.py

# Die exe wird in dist/Psykanoid.exe erstellt
```

## 🎮 Spielmodus

Beim Start des Spiels erscheint ein Menü mit zwei Optionen:

1. **SINGLEPLAYER** - Spielen Sie allein mit einem Paddle (Tasten: A/ D)
2. **2-PLAYER** - Spielen Sie mit einem Freund gleichzeitig (Tasten: A/D für Spieler 1, Pfeiltasten für Spieler 2)

Wählen Sie Ihren Modus mit der **LEERTASTE** oder beenden Sie das Spiel mit **ESC**.

## 📄 Lizenz

Dieses Projekt ist ein Hobby-Projekt.

## 📝 Technische Details

- **Game Engine**: Pygame 2.6.1
- **Python Version**: 3.12.10
- **Bildschirm**: 1024x768 Pixel
- **FPS**: 60
- **Steine**: 60 (6x10 Grid)
- **Balls**: 2 (einer pro Spieler)

## 🎨 Spielmechanik

- **Punkte**: 100 Punkte pro Stein, 20 Punkte für Teil-Treffer
- **Punktabzug**: -50 Punkte wenn ein Ball den Bildschirm verlässt
- **Game Over**: Wenn alle Steine zerstört sind
- **Sieg**: Spieler mit den meisten Punkten gewinnt

## 📁 Dateistruktur

```
Psykanoid/
├── psykanoid.py          # Hauptspiel-Datei
├── README.md             # Diese Datei
├── .venv/                # Virtuelle Umgebung
├── dist/
│   └── Psykanoid.exe     # Standalone exe
└── build/                # Build-Verzeichnis
```

## 🐛 Fehlerbehebung

### Pygame nicht gefunden
```bash
.venv\Scripts\python.exe -m pip install pygame
```

### NumPy nicht gefunden (für Sounds)
```bash
.venv\Scripts\python.exe -m pip install numpy
```

### Konsolenfenster erscheint
Stellen Sie sicher, dass `--windowed` bei der PyInstaller-Kompilierung verwendet wird.

## 📞 Support

Bei Fragen oder Problemen können Sie ein Issue auf GitHub erstellen.

---

**Viel Spaß beim Spielen!** 🎉
