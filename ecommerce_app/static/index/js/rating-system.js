// ===== SISTEMA DE CALIFICACIÓN INTERACTIVO =====
document.addEventListener('DOMContentLoaded', function() {
  // Calificaciones por defecto para cada producto
  const defaultRatings = {
    '1': 4.5, // Whole Wheat Sandwich Bread
    // Agregar más productos según sea necesario
  };

  // Función para actualizar las estrellas visualmente
  function updateStars(container, rating) {
    const stars = container.querySelectorAll('.star');
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 !== 0;

    stars.forEach((star, index) => {
      star.classList.remove('active', 'half');
      
      if (index < fullStars) {
        star.classList.add('active');
      } else if (index === fullStars && hasHalfStar) {
        star.classList.add('half');
      }
    });
  }

  // Función para mostrar mensajes de calificación
  function showRatingMessage(message, rating) {
    const notification = document.createElement('div');
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #28a745;
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 10000;
      font-weight: 500;
      transform: translateX(100%);
      transition: transform 0.3s ease;
      display: flex;
      align-items: center;
      gap: 8px;
    `;
    
    // Agregar icono de estrella
    const starIcon = document.createElement('svg');
    starIcon.innerHTML = '<use xlink:href="#star-full"></use>';
    starIcon.style.cssText = `
      width: 16px;
      height: 16px;
      fill: white;
    `;
    
    notification.appendChild(starIcon);
    notification.appendChild(document.createTextNode(message));
    
    document.body.appendChild(notification);
    
    // Animar entrada
    setTimeout(() => {
      notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remover después de 3 segundos
    setTimeout(() => {
      notification.style.transform = 'translateX(100%)';
      setTimeout(() => {
        if (document.body.contains(notification)) {
          document.body.removeChild(notification);
        }
      }, 300);
    }, 3000);
  }

  // Inicializar sistema de calificación para cada producto
  document.querySelectorAll('.rating-container').forEach(container => {
    const productId = container.getAttribute('data-product-id');
    const starsContainer = container.querySelector('.stars-container');
    
    if (starsContainer && productId) {
      // Cargar calificación guardada o usar la por defecto
      const savedRating = localStorage.getItem(`product_rating_${productId}`);
      const rating = savedRating ? parseFloat(savedRating) : defaultRatings[productId];
      updateStars(container, rating);
      
      // Event listeners para las estrellas
      starsContainer.querySelectorAll('.star').forEach(star => {
        star.addEventListener('click', function() {
          const clickedRating = parseInt(this.getAttribute('data-rating'));
          
          // Guardar calificación en localStorage
          localStorage.setItem(`product_rating_${productId}`, clickedRating.toString());
          
          // Actualizar estrellas visualmente
          updateStars(container, clickedRating);
          
          // Mostrar mensaje de confirmación
          showRatingMessage(`¡Calificación de ${clickedRating} estrellas guardada!`, clickedRating);
        });
        
        // Efectos hover
        star.addEventListener('mouseenter', function() {
          const hoverRating = parseInt(this.getAttribute('data-rating'));
          updateStars(container, hoverRating);
        });
        
        star.addEventListener('mouseleave', function() {
          const savedRating = localStorage.getItem(`product_rating_${productId}`);
          const rating = savedRating ? parseFloat(savedRating) : defaultRatings[productId];
          updateStars(container, rating);
        });
      });
    }
  });
  
  // ===== SISTEMA DE FAVORITOS PARA CORAZONES =====
  document.querySelectorAll('.product-item .btn-outline-dark').forEach(button => {
    const heartIcon = button.querySelector('svg[use*="#heart"]');
    if (heartIcon) {
      const productId = button.closest('.product-item').querySelector('.rating-container')?.getAttribute('data-product-id') || 
                       button.closest('.product-item').querySelector('h3')?.textContent?.trim() || 'unknown';
      
      // Verificar si ya está marcado como favorito
      const isFavorited = localStorage.getItem(`product_favorite_${productId}`) === 'true';
      if (isFavorited) {
        button.classList.add('favorited');
      }
      
      // Event listener para marcar/desmarcar favoritos
      button.addEventListener('click', function(e) {
        e.preventDefault();
        
        const productId = this.closest('.product-item').querySelector('.rating-container')?.getAttribute('data-product-id') || 
                         this.closest('.product-item').querySelector('h3')?.textContent?.trim() || 'unknown';
        
        const isCurrentlyFavorited = this.classList.contains('favorited');
        
        if (isCurrentlyFavorited) {
          // Desmarcar como favorito
          this.classList.remove('favorited');
          localStorage.setItem(`product_favorite_${productId}`, 'false');
          showFavoriteMessage('Producto removido de favoritos', false);
        } else {
          // Marcar como favorito
          this.classList.add('favorited');
          localStorage.setItem(`product_favorite_${productId}`, 'true');
          showFavoriteMessage('¡Producto agregado a favoritos!', true);
        }
      });
    }
  });
  
  // Función para mostrar mensajes de favoritos
  function showFavoriteMessage(message, isAdded) {
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: ${isAdded ? '#ff0000' : '#6c757d'};
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 10000;
      font-weight: 500;
      transform: translateX(100%);
      transition: transform 0.3s ease;
      display: flex;
      align-items: center;
      gap: 8px;
    `;
    
    // Agregar icono de corazón
    const heartIcon = document.createElement('svg');
    heartIcon.innerHTML = '<use xlink:href="#heart"></use>';
    heartIcon.style.cssText = `
      width: 16px;
      height: 16px;
      fill: white;
    `;
    
    notification.appendChild(heartIcon);
    notification.appendChild(document.createTextNode(message));
    
    document.body.appendChild(notification);
    
    // Animar entrada
    setTimeout(() => {
      notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remover después de 3 segundos
    setTimeout(() => {
      notification.style.transform = 'translateX(100%)';
      setTimeout(() => {
        if (document.body.contains(notification)) {
          document.body.removeChild(notification);
        }
      }, 300);
    }, 3000);
  }
}); 