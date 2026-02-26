// Set current year in footer
document.getElementById('current-year').textContent = new Date().getFullYear();

// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
            
            // Change icon based on menu state
            if (mobileMenu.classList.contains('hidden')) {
                mobileMenuButton.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="3" y1="12" x2="21" y2="12"></line>
                        <line x1="3" y1="6" x2="21" y2="6"></line>
                        <line x1="3" y1="18" x2="21" y2="18"></line>
                    </svg>
                `;
            } else {
                mobileMenuButton.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                `;
            }
        });
    }
    
    // Close mobile menu when clicking on a link
    const mobileNavLinks = document.querySelectorAll('.mobile-nav-link');
    mobileNavLinks.forEach(link => {
        link.addEventListener('click', function() {
            mobileMenu.classList.add('hidden');
            mobileMenuButton.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="3" y1="12" x2="21" y2="12"></line>
                    <line x1="3" y1="6" x2="21" y2="6"></line>
                    <line x1="3" y1="18" x2="21" y2="18"></line>
                </svg>
            `;
        });
    });
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Add active class to nav links on scroll
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link, .mobile-nav-link');
    
    function highlightNavOnScroll() {
        const scrollPosition = window.scrollY + 100;
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;
            const sectionId = section.getAttribute('id');
            
            if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                navLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === '#' + sectionId) {
                        link.classList.add('active');
                    }
                });
            }
        });
    }
    
    window.addEventListener('scroll', highlightNavOnScroll);
    
    // Animation on scroll
    const animateOnScroll = function() {
        const elements = document.querySelectorAll('.realisation-card, .actualite-card, .timeline-item, .engagement-card, .projets-card, .bio-column');
        
        elements.forEach((element, index) => {
            const elementPosition = element.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;
            
            if (elementPosition < windowHeight - 50) {
                // Add delay based on index for staggered animation
                setTimeout(() => {
                    element.classList.add('animate');
                }, index * 100);
            }
        });
    };
    
    window.addEventListener('scroll', animateOnScroll);
    
    // Initial animations
    setTimeout(animateOnScroll, 300); // Run once on page load with a slight delay
    
    // Add animate-on-scroll class to all sections
    document.querySelectorAll('.section').forEach((section, index) => {
        const elements = section.querySelectorAll('h2, h3, p, .btn');
        elements.forEach((element, elementIndex) => {
            element.classList.add('animate-on-scroll');
            element.classList.add(`delay-${(elementIndex % 5) * 100}`);
            
            // Observe element
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        setTimeout(() => {
                            entry.target.classList.add('animate');
                        }, elementIndex * 100);
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.1 });
            
            observer.observe(element);
        });
    });
    
    // Add pulse effect to buttons
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.classList.add('pulse');
        });
        
        btn.addEventListener('mouseleave', function() {
            this.classList.remove('pulse');
        });
    });
    
    // Animate flag colors
    const flagColors = document.querySelectorAll('.flag-color');
    setInterval(() => {
        flagColors.forEach((color, index) => {
            setTimeout(() => {
                color.style.transform = 'scale(1.2)';
                setTimeout(() => {
                    color.style.transform = 'scale(1)';
                }, 300);
            }, index * 200);
        });
    }, 5000);
});

// Form validation
const contactForm = document.querySelector('.contact-form form');
if (contactForm) {
    contactForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const nameInput = document.getElementById('name');
        const emailInput = document.getElementById('email');
        const subjectInput = document.getElementById('subject');
        const messageInput = document.getElementById('message');
        
        let isValid = true;
        
        // Simple validation
        if (!nameInput.value.trim()) {
            isValid = false;
            nameInput.style.borderColor = 'red';
            nameInput.classList.add('shake');
            setTimeout(() => nameInput.classList.remove('shake'), 500);
        } else {
            nameInput.style.borderColor = 'var(--border-color)';
        }
        
        if (!emailInput.value.trim() || !isValidEmail(emailInput.value)) {
            isValid = false;
            emailInput.style.borderColor = 'red';
            emailInput.classList.add('shake');
            setTimeout(() => emailInput.classList.remove('shake'), 500);
        } else {
            emailInput.style.borderColor = 'var(--border-color)';
        }
        
        if (!subjectInput.value.trim()) {
            isValid = false;
            subjectInput.style.borderColor = 'red';
            subjectInput.classList.add('shake');
            setTimeout(() => subjectInput.classList.remove('shake'), 500);
        } else {
            subjectInput.style.borderColor = 'var(--border-color)';
        }
        
        if (!messageInput.value.trim()) {
            isValid = false;
            messageInput.style.borderColor = 'red';
            messageInput.classList.add('shake');
            setTimeout(() => messageInput.classList.remove('shake'), 500);
        } else {
            messageInput.style.borderColor = 'var(--border-color)';
        }
        
        if (isValid) {
            // Here you would typically send the form data to a server
            const successMessage = document.createElement('div');
            successMessage.className = 'success-message';
            successMessage.innerHTML = `
                <div class="success-icon">✓</div>
                <p>Votre message a été envoyé avec succès!</p>
            `;
            
            contactForm.innerHTML = '';
            contactForm.appendChild(successMessage);
        }
    });
}

// Email validation helper
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Add CSS class for animations
document.addEventListener('DOMContentLoaded', function() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
            20%, 40%, 60%, 80% { transform: translateX(5px); }
        }
        
        .shake {
            animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both;
        }
        
        .success-message {
            text-align: center;
            padding: 30px;
            animation: fadeInUp 0.5s ease-out;
        }
        
        .success-icon {
            width: 60px;
            height: 60px;
            background-color: var(--green);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            margin: 0 auto 20px;
            animation: scaleIn 0.5s ease-out;
        }
        
        /* Floating animation for hero image */
        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
            100% { transform: translateY(0px); }
        }
        
        .minister-photo {
            animation: float 6s ease-in-out infinite;
        }
        
        /* Gradient animation for hero overlay */
        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .hero-overlay {
            background: linear-gradient(135deg, rgba(255, 159, 69, 0.9), rgba(255, 159, 69, 0.7), rgba(76, 175, 80, 0.8));
            background-size: 200% 200%;
            animation: gradientBG 15s ease infinite;
        }
    `;
    document.head.appendChild(style);
    
    // Add parallax effect to hero section
    const hero = document.querySelector('.hero');
    if (hero) {
        window.addEventListener('scroll', function() {
            const scrollPosition = window.scrollY;
            hero.style.backgroundPosition = `center ${scrollPosition * 0.5}px`;
        });
    }
    
    // Add hover effects to timeline items
    document.querySelectorAll('.timeline-item').forEach(item => {
        item.addEventListener('mouseenter', function() {
            const icon = this.querySelector('.timeline-icon svg');
            if (icon) {
                icon.style.transform = 'scale(1.2) rotate(10deg)';
            }
        });
        
        item.addEventListener('mouseleave', function() {
            const icon = this.querySelector('.timeline-icon svg');
            if (icon) {
                icon.style.transform = 'scale(1) rotate(0deg)';
            }
        });
    });
});