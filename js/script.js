document.addEventListener('DOMContentLoaded', () => {
    
    // ----------- 1. Scroll Reveal Animation -----------
    const revealElements = document.querySelectorAll('.reveal');

    const revealCallback = (entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
                // Optionnel : ne plus observer une fois apparu pour garder l'état 'active'
                // observer.unobserve(entry.target); 
            }
        });
    };

    const revealOptions = {
        threshold: 0.1, // Déclenche quand 10% de l'élément est visible
        rootMargin: "0px 0px -50px 0px"
    };

    const revealObserver = new IntersectionObserver(revealCallback, revealOptions);

    revealElements.forEach(el => {
        revealObserver.observe(el);
    });

    // ----------- 2. Dynamic Navbar Glass Effect -----------
    const navbar = document.querySelector('.navbar');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // ----------- 3. Mobile Menu Toggle (Basic) -----------
    const burger = document.querySelector('.burger-menu');
    // Une implémentation complète du menu mobile serait nécessaire ici
    // On l'ajoute comme simple alerte pour l'instant si cliqué
    if(burger) {
        burger.addEventListener('click', () => {
            alert('Ouverture du menu mobile à implémenter si besoin');
            // Logique typique : toggle class sur nav-links
        });
    }

    // ----------- 4. Smooth Scrolling for Anchor Links -----------
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if(targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if(targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

});
