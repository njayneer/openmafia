// Pobranie wszystkich elementów przycisków "x"
const closeButtons = document.querySelectorAll('.close');

// Dodanie obsługi zdarzenia dla każdego przycisku "x"
closeButtons.forEach(button => {
  button.addEventListener('click', () => {
    // Ukrycie elementu alertu
    button.parentNode.style.display = 'none';
  });
});
