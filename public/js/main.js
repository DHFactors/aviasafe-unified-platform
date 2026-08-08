/* ============================================================================
   FILE: main.js
   PATH: public/js/main.js
   VERSION: 1.0.0
   DATE CREATED: 2026-08-06
   PURPOSE: Shared UI behaviour for the AviaSAFE platform — footer year,
            active navigation highlighting and mobile nav toggle.
            Non-destructive: safe to load on any page that uses main.css/global.css.
   AUTHOR: AviaSAFE Systems
   ============================================================================ */

(function() {
    'use strict';

    function onReady(fn) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', fn);
        } else {
            fn();
        }
    }

    onReady(function() {
        // Footer year
        var yearEls = document.querySelectorAll('[data-year]');
        var year = String(new Date().getFullYear());
        yearEls.forEach(function(el) {
            el.textContent = year;
        });

        // Active nav highlight based on current path
        var path = window.location.pathname;
        var navLinks = document.querySelectorAll('.app-header nav a');
        navLinks.forEach(function(link) {
            var href = link.getAttribute('href') || '';
            if (href === '/' && path === '/') {
                link.classList.add('active');
            } else if (href.indexOf('.html') !== -1 && path.indexOf(href) !== -1) {
                link.classList.add('active');
            }
        });

        // Mobile nav toggle
        var toggle = document.querySelector('.nav-toggle');
        var nav = document.querySelector('.app-header nav');
        if (toggle && nav) {
            toggle.addEventListener('click', function() {
                nav.classList.toggle('open');
                toggle.classList.toggle('open');
            });
        }

        // Hero screenshot gallery rotation
        var images = document.querySelectorAll('.gallery-image');
        var dots = document.querySelectorAll('.dot');
        if (images.length > 0) {
            var currentIndex = 0;
            var interval = null;

            function showImage(index) {
                images.forEach(function(img) { img.classList.remove('active'); });
                dots.forEach(function(dot) { dot.classList.remove('active'); });

                images[index].classList.add('active');
                if (dots[index]) dots[index].classList.add('active');
                currentIndex = index;
            }

            function nextImage() {
                showImage((currentIndex + 1) % images.length);
            }

            function startRotation() {
                if (interval) clearInterval(interval);
                interval = setInterval(nextImage, 5000);
            }

            startRotation();

            dots.forEach(function(dot, index) {
                dot.addEventListener('click', function() {
                    startRotation();
                    showImage(index);
                });
            });
        }
    });
})();
