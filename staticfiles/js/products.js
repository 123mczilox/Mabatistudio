// Products page interactions for MabatiHubKenya

document.addEventListener('DOMContentLoaded', () => {
    // Smooth scroll when clicking category cards
    const categoryButtons = document.querySelectorAll('[data-target-section]');
    categoryButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetId = button.getAttribute('data-target-section');
            const target = document.getElementById(targetId);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // Smooth scroll for anchor links on the page
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', event => {
            const href = link.getAttribute('href');
            if (href.length > 1) {
                const target = document.querySelector(href);
                if (target) {
                    event.preventDefault();
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        });
    });

    // Highlight active product card while scrolling
    const sections = document.querySelectorAll('.product-section');
    const navCards = document.querySelectorAll('[data-target-section]');

    const setActiveCard = () => {
        const offset = window.innerHeight * 0.35;
        sections.forEach(section => {
            const rect = section.getBoundingClientRect();
            const id = section.id;
            if (rect.top <= offset && rect.bottom >= offset) {
                navCards.forEach(card => {
                    card.classList.toggle('active-card', card.getAttribute('data-target-section') === id);
                });
            }
        });
    };

    setActiveCard();
    window.addEventListener('scroll', setActiveCard);
});
