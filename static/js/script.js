class SmartDebouncer {
    constructor(delay = 300) {
        this.delay = delay;
        this.timeout = null;
    }
    call(fn) {
        clearTimeout(this.timeout);
        this.timeout = setTimeout(fn, this.delay);
    }
}

class AppState {
    constructor() {
        this.items = [];
        this.cart = [];
        this.activeCategory = 'all';
        this.searchQuery = '';
    }
    total() {
        return this.cart.reduce((s, i) => s + i.price * i.count, 0);
    }
    count() {
        return this.cart.reduce((s, i) => s + i.count, 0);
    }
}

class CartService {
    constructor(state, onChange) {
        this.state = state;
        this.onChange = onChange;
    }
    add(id) {
        const item = this.state.items.find(i => i.id === id);
        if (!item) return;
        const ci = this.state.cart.find(c => c.id === id);
        if (ci) ci.count++;
        else this.state.cart.push({ ...item, count: 1 });
        this.onChange();
    }
    change(id, delta) {
        const ci = this.state.cart.find(c => c.id === id);
        if (!ci) return;
        ci.count += delta;
        if (ci.count <= 0) this.state.cart = this.state.cart.filter(c => c.id !== id);
        this.onChange();
    }
    toPayload() {
        return this.state.cart.map(i => ({ id: i.id, name: i.name, price: i.price, count: i.count }));
    }
}

class ViewRenderer {
    constructor(state, cartService) {
        this.state = state;
        this.cartService = cartService;
        this.debouncer = new SmartDebouncer(120);
    }
    showSpinner(show) {
        let el = document.getElementById('global-spinner');
        if (show) {
            if (!el) {
                el = document.createElement('div');
                el.id = 'global-spinner';
                el.className = 'global-spinner';
                el.innerHTML = '<div class="spinner"></div>';
                document.body.appendChild(el);
            }
        } else if (el) {
            el.remove();
        }
    }
    showToast(msg) {
        const toast = document.getElementById('toast');
        if (!toast) return;
        toast.innerText = msg;
        toast.classList.add('visible');
        setTimeout(() => toast.classList.remove('visible'), 3000);
    }
    renderCategories(list) {
        const section = document.getElementById('categories-section');
        if (!section) return;
        section.innerHTML = '';
        const allBtn = document.createElement('button');
        allBtn.className = 'chip' + (this.state.activeCategory === 'all' ? ' active' : '');
        allBtn.textContent = 'All';
        allBtn.onclick = () => { App.filterCategory(allBtn, 'all'); };
        section.appendChild(allBtn);
        (list || []).forEach(cat => {
            if (!cat) return;
            // All categories are in English
            const categoryName = cat;
            const btn = document.createElement('button');
            btn.className = 'chip' + (this.state.activeCategory === categoryName ? ' active' : '');
            btn.textContent = categoryName;
            btn.onclick = () => { App.filterCategory(btn, categoryName); };
            section.appendChild(btn);
        });
    }
    renderSkeletons() {
        const loader = document.getElementById('loader');
        if (!loader) return;
        let html = '';
        for (let i = 0; i < 6; i++) {
            html += `<div class="menu-item"><div class="item-image-box skeleton"></div><div class="skeleton" style="height:14px;width:70%;margin-bottom:8px"></div><div class="skeleton" style="height:10px;width:90%;margin-bottom:4px"></div><div class="skeleton" style="height:10px;width:50%;margin-top:auto"></div></div>`;
        }
        loader.innerHTML = html;
    }
    renderMenu() {
        const grid = document.getElementById('menu-grid');
        if (!grid) return;
        grid.innerHTML = '';
        let items = this.state.items.slice();
        if (this.state.activeCategory !== 'all') items = items.filter(i => i.category === this.state.activeCategory);
        if (this.state.searchQuery) items = items.filter(i => i.name.toLowerCase().includes(this.state.searchQuery.toLowerCase()));
        if (items.length === 0) {
            grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;color:var(--color-text-secondary);padding:40px">No items found</div>';
            return;
        }
        items.forEach((item, idx) => {
            const inCart = (this.state.cart.find(c => c.id === item.id) || {}).count || 0;
            const el = document.createElement('div');
            el.className = 'menu-item ' + (inCart > 0 ? 'in-cart' : '');
            el.innerHTML = `<div class="item-image-box"><span class="item-emoji">${item.emoji || '🌯'}</span></div><div class="item-info"><div class="item-title">${item.name}</div><div class="item-desc">${item.description || ''}</div><div class="item-footer"><span class="item-price">${item.price} $</span></div></div>`;
            const btn = document.createElement('button');
            btn.className = 'btn-add-mini';
            btn.textContent = inCart > 0 ? inCart : '+';
            btn.onclick = (e) => { e.stopPropagation(); this.cartService.add(item.id); };
            const footer = el.querySelector('.item-footer');
            footer.appendChild(btn);
            el.onclick = () => { this.openProductModal(item); this.state.selectedId = item.id; };
            grid.appendChild(el);
        });
    }
    updateCartUI() {
        const total = this.state.cart.reduce((s, i) => s + i.price * i.count, 0);
        const count = this.state.cart.reduce((s, i) => s + i.count, 0);
        
        const mainBtn = document.getElementById('cart-main-btn');
        if (mainBtn) {
            if (count > 0) {
                mainBtn.classList.add('active');
                mainBtn.innerHTML = `Confirm Order • ${total} $`;
                mainBtn.style.pointerEvents = 'auto';
            } else {
                mainBtn.classList.remove('active');
                mainBtn.innerHTML = `Cart is Empty`;
                mainBtn.style.pointerEvents = 'none';
            }
        }

        this.renderMenu();

        const cartModal = document.getElementById('modal-cart');
        if (cartModal && cartModal.classList.contains('active')) {
            this.renderCartList();
        }
    }
    openProductModal(item) {
        const modal = document.getElementById('modal-product');
        if (!modal) return;
        document.getElementById('modal-title').innerText = item.name;
        document.getElementById('modal-desc').innerText = item.description || '';
        document.getElementById('modal-price').innerText = `${item.price} $`;
        this.state.selectedId = item.id;
        modal.classList.add('active');
    }
    openCartModal() {
        if (this.state.cart.length === 0) return;
        const modal = document.getElementById('modal-cart');
        if (!modal) return;
        this.renderCartList();
        modal.classList.add('active');
    }
    renderCartList() {
        const list = document.getElementById('cart-list');
        const totalEl = document.getElementById('cart-modal-total');
        if (!list || !totalEl) return;
        const total = this.state.cart.reduce((s, i) => s + i.price * i.count, 0);
        totalEl.innerText = `${total} $`;
        list.innerHTML = '';
        this.state.cart.forEach(item => {
            const el = document.createElement('div');
            el.className = 'cart-item';
            const controls = document.createElement('div');
            controls.className = 'cart-controls';
            const minus = document.createElement('button');
            minus.className = 'cart-btn-mini';
            minus.textContent = '-';
            minus.onclick = () => this.cartService.change(item.id, -1);
            const plus = document.createElement('button');
            plus.className = 'cart-btn-mini';
            plus.textContent = '+';
            plus.onclick = () => this.cartService.change(item.id, 1);
            const countSpan = document.createElement('span');
            countSpan.style = 'font-size:14px; font-weight:600; min-width:20px; text-align:center;';
            countSpan.id = `cart-count-${item.id}`;
            countSpan.textContent = item.count;
            controls.appendChild(minus);
            controls.appendChild(countSpan);
            controls.appendChild(plus);
            el.innerHTML = `<div style="flex-grow:1"><div style="font-weight:600">${item.name}</div><div style="font-size:12px;color:var(--color-text-secondary)">${item.price} $ per item</div></div>`;
            el.appendChild(controls);
            list.appendChild(el);
        });
    }
}

const App = (function () {
    const tg = window.Telegram ? window.Telegram.WebApp : null;
    const state = new AppState();
    let cartService, renderer;
    const debouncer = new SmartDebouncer(150);

    async function init() {
        if (tg) {
            tg.ready();
            tg.expand();
            tg.enableClosingConfirmation();
            tg.onEvent && tg.onEvent('themeChanged', applyTheme);
        }
        applyTheme();
        cartService = new CartService(state, () => renderer.updateCartUI());
        renderer = new ViewRenderer(state, cartService);
        renderer.renderSkeletons();
        bindUi();
    }
    function applyTheme() {
        const body = document.body;
        const params = tg && tg.themeParams;
        const colorScheme = tg && tg.colorScheme;
        if (colorScheme === 'light') body.classList.add('light-mode'); else body.classList.remove('light-mode');
        if (params) {
            body.classList.add('tg-theme');
            const setVar = (n, v) => v && document.documentElement.style.setProperty(n, v);
            setVar('--tg-theme-bg-color', params.bg_color);
            setVar('--tg-theme-text-color', params.text_color);
            setVar('--tg-theme-hint-color', params.hint_color);
            setVar('--tg-theme-button-color', params.button_color);
            setVar('--tg-theme-button-text-color', params.button_text_color);
        }
    }
    function bindUi() {
        document.getElementById('landing')?.addEventListener('click', () => switchToMenu());
        document.getElementById('cart-main-btn')?.addEventListener('click', () => renderer.openCartModal());
        document.getElementById('add-from-modal')?.addEventListener('click', () => { cartService.add(state.selectedId); renderer.updateCartUI(); renderer.closeProductModal && renderer.closeProductModal(); });
        document.getElementById('modal-cart')?.addEventListener('click', (e) => { if (e.target === e.currentTarget) closeModals(); });
        document.getElementById('modal-product')?.addEventListener('click', (e) => { if (e.target === e.currentTarget) closeModals(); });
        const searchInput = document.getElementById('search-input');
        if (searchInput) searchInput.addEventListener('input', (e) => { state.searchQuery = e.target.value; debouncer.call(() => renderer.renderMenu()); });
    }
    async function switchToMenu() {
        document.getElementById('landing')?.classList.remove('active');
        document.getElementById('menu-screen')?.classList.add('active');
        await fetchData();
    }
    async function fetchData() {
        const menuEl = document.getElementById('menu-grid');
        const loaderEl = document.getElementById('loader');
        if (menuEl) menuEl.classList.remove('loaded');
        if (loaderEl) renderer.renderSkeletons();
        renderer.showSpinner(true);
        try {
            const resp = await fetch('/api/menu');
            if (!resp.ok) throw new Error('Backend offline');
            const data = await resp.json();
            state.items = data;
            renderer.renderMenu();
            if (menuEl) menuEl.classList.add('loaded');
            const cResp = await fetch('/api/categories');
            if (cResp.ok) renderer.renderCategories(await cResp.json());
        } catch (e) {
            console.error(e);
            renderer.showToast('Menu loading error. Demo mode.');
            state.items = [
                {id: 1, name: "Classic Kebab", price: 120, description: "Chicken, cucumber, tomatoes, house sauce", category: "Classic", emoji: "🌯"}
            ];
            renderer.renderMenu();
            if (menuEl) menuEl.classList.add('loaded');
        } finally {
            renderer.showSpinner(false);
        }
    }
    function closeModals() { document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active')); }
    async function checkout() {
        if (state.cart.length === 0) return;

        const btn = document.querySelector('button[onclick="App.checkout()"]');
        const originalText = btn ? btn.innerText : '';
        if(btn) btn.innerText = 'Loading...';

        try {
            const res = await fetch('/api/create-invoice', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cart: state.cart })
            });

            const result = await res.json();

            if (result.error) {
                alert('Error: ' + result.error);
                if(btn) btn.innerText = originalText;
                return;
            }

            if (result.invoice_link) {
                closeModals();
                
                if (window.Telegram.WebApp.isVersionAtLeast('6.1')) {
                    window.Telegram.WebApp.openInvoice(result.invoice_link, function(status) {
                        if (status === 'paid') {
                            window.Telegram.WebApp.close();
                        } else if (status === 'cancelled') {
                            // User cancelled payment
                        } else if (status === 'failed') {
                            alert('Payment failed.');
                        }
                    });
                } else {
                    window.location.href = result.invoice_link;
                }
            }
        } catch (e) {
            console.error(e);
            alert('Network or server error occurred.');
        } finally {
            if(btn) btn.innerText = originalText;
        }
    }
    function toggleSearch() {
        const header = document.getElementById('header-content');
        const search = document.getElementById('search-container');
        const input = document.getElementById('search-input');
        if (search.classList.contains('active')) {
            search.classList.remove('active');
            header && (header.style.display = 'flex');
            state.searchQuery = '';
            if (input) input.value = '';
            renderer.renderMenu();
        } else {
            header && (header.style.display = 'none');
            search.classList.add('active');
            input && input.focus();
        }
    }
    function onSearchInput(val) {
        state.searchQuery = val;
        debouncer.call(() => renderer.renderMenu());
    }
    function filterCategory(btn, category) {
        document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
        btn && btn.classList.add('active');
        state.activeCategory = category;
        renderer.renderMenu();
    }
    function addToCartFromModal() {
        if (state.selectedId) {
            cartService.add(state.selectedId);
            closeModals();
        }
    }
    function openCartModal() { renderer.openCartModal(); }
    function closeModals() { document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active')); }

    return {
        init,
        switchToMenu,
        toggleSearch,
        onSearchInput,
        filterCategory,
        addToCart: (id) => { cartService.add(id); },
        addToCartFromModal,
        handleCartChange: (id, delta) => { cartService.change(id, delta); },
        openCartModal,
        closeModals,
        checkout
    };
})();

document.addEventListener('DOMContentLoaded', () => { App.init(); });

window.App = window.App || App;
