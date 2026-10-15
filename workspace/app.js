const items = ['Item 1', 'Item 2', 'Item 3'];
const list = document.getElementById('items');

items.forEach((text) => {
  const li = document.createElement('li');
  li.textContent = text;
  list.appendChild(li);
});
