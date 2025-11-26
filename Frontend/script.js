/**
 * DraftCraft Frontend Logic
 * Handhabt das Hamburger Menü und den Theme Switcher
 */

// 1. Theme Switcher Funktion
function setTheme(themeName) {
    // Ändert die Klasse im <body> Tag, wodurch CSS Variablen neu geladen werden
    document.body.className = themeName;
}

// 2. Warte bis das Dokument geladen ist
document.addEventListener('DOMContentLoaded', () => {
    const hamburgerBtn = document.getElementById('hamburgerBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    
    let isMenuOpen = false;

    // Klick auf Hamburger Icon
    hamburgerBtn.addEventListener('click', () => {
        isMenuOpen = !isMenuOpen;
        toggleMenu(isMenuOpen);
    });

    // Schließen beim Klick auf einen Link
    const mobileLinks = document.querySelectorAll('.mobile-link');
    mobileLinks.forEach(link => {
        link.addEventListener('click', () => {
            isMenuOpen = false;
            toggleMenu(false);
        });
    });

    // Hilfsfunktion für Menü-Status
    function toggleMenu(open) {
        if (open) {
            mobileMenu.classList.add('active');
            // Animiere Icon zu einem X
            hamburgerBtn.children[0].style.transform = 'rotate(45deg) translate(5px, 6px)';
            hamburgerBtn.children[1].style.opacity = '0';
            hamburgerBtn.children[2].style.transform = 'rotate(-45deg) translate(5px, -6px)';
        } else {
            mobileMenu.classList.remove('active');
            // Reset Icon
            hamburgerBtn.children[0].style.transform = 'none';
            hamburgerBtn.children[1].style.opacity = '1';
            hamburgerBtn.children[2].style.transform = 'none';
        }
    }
});