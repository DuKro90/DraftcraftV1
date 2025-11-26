# DraftCraft Frontend Implementierung & Baukasten

Diese Datei enthält den vollständigen Quellcode und die Implementierungsanleitung für das DraftCraft Frontend-System. 

**Inhalt:**
1. `index.html` (Struktur & Layout)
2. `style.css` (Themes, Design System & Responsivität)
3. `script.js` (Interaktivität: Menü & Theme-Wechsel)

---

## 1. HTML Struktur (`index.html`)

Erstelle eine Datei namens `index.html` und füge folgenden Code ein:

```html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DraftCraft - AI Proposal Software</title>
    <link href="[https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap](https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap)" rel="stylesheet">
    <link rel="stylesheet" href="style.css">
</head>
<body class="theme-copper">

    <header class="site-header">
        <div class="container header-inner">
            <div class="logo">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 19l7-7 3 3-7 7-3-3z"></path>
                    <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"></path>
                    <path d="M2 2l7.586 7.586"></path>
                    <circle cx="11" cy="11" r="2"></circle>
                </svg>
                <span class="logo-text">DraftCraft</span>
            </div>

            <nav class="desktop-nav">
                <a href="#">Features</a>
                <a href="#">Pricing</a>
                <a href="#">Contact</a>
            </nav>

            <div class="header-actions">
                <a href="#" class="nav-link-secondary">Log in</a>
                <button class="btn btn-primary">Get Started</button>
            </div>
            
            <button class="hamburger-btn" id="hamburgerBtn" aria-label="Menü öffnen">
                <span></span>
                <span></span>
                <span></span>
            </button>
        </div>
    </header>

    <div class="mobile-menu-overlay" id="mobileMenu">
        <nav class="mobile-nav-links">
            <a href="#" class="mobile-link">Features</a>
            <a href="#" class="mobile-link">Pricing</a>
            <a href="#" class="mobile-link">Contact</a>
            <hr style="opacity: 0.2; margin: 1rem 0; border-color: white;">
            <a href="#" class="mobile-link">Log in</a>
            <button class="btn btn-primary full-width">Get Started</button>
        </nav>
    </div>

    <section class="hero">
        <div class="container hero-content">
            <h1 class="hero-headline">Streamline Your Proposals</h1>
            <p class="hero-subheadline">AI-Powered Software for Faster Estimates</p>
            
            <div class="hero-visual">
                <div class="icon-circle-large">
                    <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="var(--accent-500)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 19l7-7 3 3-7 7-3-3z"></path>
                        <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"></path>
                        <path d="M2 2l7.586 7.586"></path>
                    </svg>
                </div>
            </div>

            <h2 class="brand-name">DraftCraft</h2>
            <p class="hero-desc">AI-Powered Software for Proposal Support</p>
            
            <div class="cta-group">
                <button class="btn btn-primary">Get Started</button>
                <button class="btn btn-outline">View Demo</button>
            </div>
        </div>
    </section>

    <section class="section-features">
        <div class="container">
            <h3 class="section-title">Komponenten & Themes Baukasten</h3>
            
            <div class="theme-switcher-container">
                <p>Theme testen:</p>
                <div class="theme-buttons">
                    <button onclick="setTheme('theme-blue')" title="Blue" style="background:#0F3558;"></button>
                    <button onclick="setTheme('theme-copper')" title="Copper" style="background:#1B1D1F;"></button>
                    <button onclick="setTheme('theme-teal')" title="Teal" style="background:#0E4D4A;"></button>
                    <button onclick="setTheme('theme-yellow')" title="Yellow" style="background:#F5C400;"></button>
                </div>
            </div>

            <div class="grid-3">
                <div class="card">
                    <h4>Smart Automation</h4>
                    <p>Generiere Vorschläge automatisch basierend auf deinen Eingaben.</p>
                </div>
                
                <div class="card">
                    <h4>Eingabefelder</h4>
                    <div class="form-group">
                        <label>Projektname</label>
                        <input type="text" class="input-field" placeholder="z.B. Webseite Relaunch">
                    </div>
                </div>

                 <div class="card">
                    <h4>Analytics</h4>
                    <p>Behalte den Überblick über gesendete Angebote und Conversion-Rates.</p>
                </div>
            </div>
        </div>
    </section>

    <script src="script.js"></script>
</body>
</html>