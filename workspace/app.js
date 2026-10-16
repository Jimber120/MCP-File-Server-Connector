// Session 6: 100-item grocery catalog generator.
// Names are fixed and prices come from a seeded PRNG, so the catalog is
// "random-looking" but identical on every page load.

const CATALOG = [
  { category: 'Produce', priceRange: [1, 6], names: [
    'Organic Bananas', 'Gala Apples', 'Baby Spinach', 'Roma Tomatoes', 'Red Onions',
    'Russet Potatoes', 'Broccoli Crowns', 'Baby Carrots', 'Avocados', 'Seedless Grapes',
    'Fresh Lemons', 'Bell Peppers', 'Cucumbers', 'Strawberries', 'Sweet Corn',
  ] },
  { category: 'Dairy', priceRange: [2, 8], names: [
    'Whole Milk', 'Skim Milk', 'Unsalted Butter', 'Greek Yogurt', 'Cheddar Cheese',
    'Mozzarella Shreds', 'Cream Cheese', 'Large Eggs', 'Sour Cream', 'Heavy Cream',
    'Cottage Cheese', 'Almond Milk',
  ] },
  { category: 'Bakery', priceRange: [2, 7], names: [
    'Sourdough Loaf', 'Whole Wheat Bread', 'Plain Bagels', 'Butter Croissants',
    'Blueberry Muffins', 'Flour Tortillas', 'Hamburger Buns', 'Cinnamon Rolls',
    'Baguette', 'Chocolate Chip Cookies',
  ] },
  { category: 'Beverages', priceRange: [2, 12], names: [
    'Orange Juice', 'Sparkling Water', 'Ground Coffee', 'Green Tea Bags', 'Cola 12-Pack',
    'Apple Juice', 'Lemonade', 'Cold Brew Coffee', 'Coconut Water', 'Ginger Ale',
    'Energy Drink', 'Bottled Water 24-Pack',
  ] },
  { category: 'Pantry', priceRange: [1, 10], names: [
    'Spaghetti Pasta', 'Jasmine Rice', 'Olive Oil', 'Black Beans', 'Tomato Sauce',
    'Peanut Butter', 'Strawberry Jam', 'All-Purpose Flour', 'Granulated Sugar', 'Sea Salt',
    'Chicken Broth', 'Rolled Oats', 'Honey', 'Canned Tuna', 'Maple Syrup',
  ] },
  { category: 'Meat', priceRange: [5, 20], names: [
    'Chicken Breast', 'Ground Beef', 'Pork Chops', 'Bacon Strips', 'Salmon Fillets',
    'Turkey Slices', 'Italian Sausage', 'Ribeye Steak', 'Shrimp', 'Whole Chicken',
  ] },
  { category: 'Snacks', priceRange: [2, 7], names: [
    'Potato Chips', 'Tortilla Chips', 'Salted Pretzels', 'Microwave Popcorn', 'Trail Mix',
    'Granola Bars', 'Dark Chocolate Bar', 'Salted Peanuts', 'Cheese Crackers',
    'Gummy Bears', 'Rice Cakes',
  ] },
  { category: 'Frozen', priceRange: [3, 10], names: [
    'Frozen Pizza', 'Vanilla Ice Cream', 'Frozen Peas', 'Chicken Nuggets',
    'Frozen Waffles', 'Mixed Berries', 'Fish Sticks', 'French Fries',
  ] },
  { category: 'Household', priceRange: [2, 15], names: [
    'Paper Towels', 'Dish Soap', 'Laundry Detergent', 'Trash Bags', 'Aluminum Foil',
    'Toilet Paper', 'Sponges',
  ] },
];

// Small seeded PRNG (mulberry32) so prices are reproducible.
function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function generateGroceryItems(seed = 20261016) {
  const rand = mulberry32(seed);
  const endings = [0.29, 0.49, 0.79, 0.99];
  const result = [];
  let id = 1;
  CATALOG.forEach(({ category, priceRange, names }) => {
    const [min, max] = priceRange;
    names.forEach((name) => {
      const dollars = min + Math.floor(rand() * (max - min + 1));
      const cents = endings[Math.floor(rand() * endings.length)];
      result.push({
        id: id++,
        name,
        category,
        price: '$' + (dollars + cents).toFixed(2),
        purchased: false,
      });
    });
  });
  return result;
}

const groceryItems = generateGroceryItems();

// Sanity checks: exactly 100 items with unique ids and names.
if (
  groceryItems.length !== 100 ||
  new Set(groceryItems.map((i) => i.id)).size !== 100 ||
  new Set(groceryItems.map((i) => i.name)).size !== 100
) {
  console.warn('Catalog check failed: expected 100 unique items, got', groceryItems.length);
}

// Rendering. All visual styling lives in style.css; this code only sets classes.
const list = document.getElementById('items');

function renderItem(item) {
  const li = document.createElement('li');
  li.className = 'item';
  li.dataset.id = String(item.id);

  const name = document.createElement('span');
  name.className = 'item-name';
  name.textContent = item.name;

  const badge = document.createElement('span');
  badge.className = 'badge badge-' + item.category.toLowerCase();
  badge.textContent = item.category;

  const price = document.createElement('span');
  price.className = 'item-price';
  price.textContent = item.price;

  li.append(name, badge, price);

  // State lives in the item object; the DOM is just a view of it. Apply the
  // current state now so a re-render (after filtering) keeps the strike-through.
  applyPurchasedState(li, item);

  li.addEventListener('click', () => {
    item.purchased = !item.purchased;
    applyPurchasedState(li, item);
    updateSummary();
  });

  return li;
}

function applyPurchasedState(li, item) {
  // The .purchased class drives the dimming and strike-through in style.css.
  li.classList.toggle('purchased', item.purchased);
}

// Session 8: live search + category filter.
// groceryItems is never mutated by filtering, only read. The visible list is
// derived from it on every change, so each item's `purchased` flag survives.
const searchInput = document.getElementById('searchInput');
const categoryFilter = document.getElementById('categoryFilter');
const itemCount = document.getElementById('itemCount');
const emptyState = document.getElementById('emptyState');

// Session 9: summary bar elements.
const summaryShown = document.getElementById('summaryShown');
const summaryPurchased = document.getElementById('summaryPurchased');
const summaryTotal = document.getElementById('summaryTotal');

// Prices are "$x.xx" strings; work in whole cents to avoid floating-point drift.
function parsePriceCents(price) {
  return Math.round(parseFloat(String(price).replace(/[^0-9.]/g, '')) * 100);
}

function formatMoney(cents) {
  return '$' + (cents / 100).toFixed(2);
}

// "Displayed" reflects the current filter; "Purchased" and the dollar total
// cover all 100 items, whether or not they are currently visible.
function updateSummary() {
  const purchased = groceryItems.filter((item) => item.purchased);
  const totalCents = purchased.reduce((sum, item) => sum + parsePriceCents(item.price), 0);
  if (summaryShown) {
    summaryShown.textContent = getFilteredItems().length + ' of ' + groceryItems.length;
  }
  if (summaryPurchased) {
    summaryPurchased.textContent =
      purchased.length + (purchased.length === 1 ? ' item' : ' items');
  }
  if (summaryTotal) summaryTotal.textContent = formatMoney(totalCents);
}

function getFilteredItems() {
  const query = searchInput ? searchInput.value.trim().toLowerCase() : '';
  const category = categoryFilter ? categoryFilter.value : 'all';
  return groceryItems.filter(
    (item) =>
      (category === 'all' || item.category === category) &&
      (query === '' || item.name.toLowerCase().includes(query))
  );
}

function renderList() {
  const visible = getFilteredItems();
  const fragment = document.createDocumentFragment();
  visible.forEach((item) => fragment.appendChild(renderItem(item)));
  list.replaceChildren(fragment);
  // Show the empty-state message only when the filters match nothing.
  if (emptyState) emptyState.hidden = visible.length > 0;
  if (itemCount) {
    itemCount.textContent =
      'Showing: ' + visible.length + (visible.length === 1 ? ' item' : ' items');
  }
  updateSummary();
}

if (searchInput) searchInput.addEventListener('input', renderList);
if (categoryFilter) categoryFilter.addEventListener('change', renderList);

renderList();

// Exposed for debugging in the browser console.
window.groceryItems = groceryItems;
