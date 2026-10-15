const items = ['Item 1', 'Item 2', 'Item 3'];
const list = document.getElementById('items');

items.forEach((text) => {
  const li = document.createElement('li');
  li.textContent = text;
  li.style.cursor = 'pointer';
  li.addEventListener('click', () => {
    li.style.textDecoration =
      li.style.textDecoration === 'line-through' ? '' : 'line-through';
  });
  list.appendChild(li);
});
