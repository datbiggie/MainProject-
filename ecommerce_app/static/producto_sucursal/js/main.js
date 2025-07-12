/*
Template Name: EventGrids - Conference and Event HTML Template.
Author: GrayGrids
*/

(function () {
    //===== Prealoder

    window.onload = function () {
        window.setTimeout(fadeout, 500);
    }

    function fadeout() {
        const preloader = document.querySelector('.preloader');
        if (preloader) {
            preloader.style.opacity = '0';
            preloader.style.display = 'none';
        }
    }


    /*=====================================
    Sticky
    ======================================= */
    window.onscroll = function () {
        var header_navbar = document.querySelector(".navbar-area");
        if (header_navbar) {
            var sticky = header_navbar.offsetTop;
            if (window.pageYOffset > sticky) {
                header_navbar.classList.add("sticky");
            } else {
                header_navbar.classList.remove("sticky");
            }
        }
        var backToTo = document.querySelector(".scroll-top");
        if (backToTo) {
            if (document.body.scrollTop > 50 || document.documentElement.scrollTop > 50) {
                backToTo.style.display = "flex";
            } else {
                backToTo.style.display = "none";
            }
        }
    };

    // WOW active
    if (typeof WOW !== 'undefined') {
        new WOW().init();
    }

    //===== mobile-menu-btn
    let navbarToggler = document.querySelector(".mobile-menu-btn");
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function () {
            navbarToggler.classList.toggle("active");
        });
    }

    // Previsualización de imagen para el modal de edición
    function previewEditImage(input) {
        console.log('Función previewEditImage llamada');
        const container = input.closest('.file-upload-container');
        const preview = document.getElementById('edit_imagePreview');
        const file = input.files[0];
        
        console.log('Archivo seleccionado:', file);
        
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                console.log('Imagen cargada en el reader');
                const img = document.createElement('img');
                img.src = e.target.result;
                img.alt = 'Preview';
                img.style.width = '100%';
                img.style.height = '100%';
                img.style.objectFit = 'contain';
                preview.innerHTML = '';
                preview.appendChild(img);
                preview.style.display = 'block';
                container.classList.add('has-image');
                const placeholder = container.querySelector('.file-upload-placeholder');
                if (placeholder) {
                    placeholder.style.display = 'none';
                }
                console.log('Previsualización actualizada');
            };
            reader.readAsDataURL(file);
        } else {
            console.log('No se seleccionó ningún archivo');
            preview.innerHTML = '';
            preview.style.display = 'none';
            container.classList.remove('has-image');
            const placeholder = container.querySelector('.file-upload-placeholder');
            if (placeholder) {
                placeholder.style.display = 'flex';
            }
        }
    }

    // Event delegation para el input de imagen
    document.addEventListener('change', function(e) {
        if (e.target && e.target.id === 'edit_imagen_producto') {
            console.log('Evento change detectado en edit_imagen_producto');
            previewEditImage(e.target);
        }
    });

    // También agregar el evento cuando el modal se abre
    document.addEventListener('DOMContentLoaded', function() {
        // Evento para cuando el modal se abre
        const editModal = document.getElementById('EditProductModal');
        if (editModal) {
            editModal.addEventListener('shown.bs.modal', function() {
                console.log('Modal abierto, agregando evento de imagen');
                const editImageInput = document.getElementById('edit_imagen_producto');
                if (editImageInput) {
                    editImageInput.addEventListener('change', function() {
                        console.log('Evento change en modal abierto');
                        previewEditImage(this);
                    });
                }
            });
        }
    });

})();