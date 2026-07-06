(function () {
    const config = window.SALE_FORM_CONFIG || {};
    const body = document.getElementById('line-items-body');
    const template = document.getElementById('line-item-template');
    const saleTotalEl = document.getElementById('sale-total');
    const dueAmountEl = document.getElementById('due-amount');
    const paymentStatusEl = document.getElementById('payment-status');
    const paidAmount = document.getElementById('paid_amount');
    const paymentMethod = document.getElementById('payment_method');
    const customerSelect = document.getElementById('customer_id');
    const searchInput = document.getElementById('product-search');
    const searchResults = document.getElementById('product-search-results');
    const emptyCartMessage = document.getElementById('empty-cart-message');
    const completeBtn = document.getElementById('complete-sale-btn');
    const saleForm = document.getElementById('sale-form');

    if (!body || !template) return;

    let searchTimer = null;
    let paidAmountTouched = false;

    function formatMoney(value) {
        return '৳' + value.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }

    function rowSubtotal(row) {
        const qty = parseFloat(row.querySelector('.quantity-input')?.value || '0');
        const price = parseFloat(row.querySelector('.price-input')?.value || '0');
        const discount = parseFloat(row.querySelector('.discount-input')?.value || '0');
        const subtotal = (qty * price) - discount;
        return subtotal > 0 ? subtotal : 0;
    }

    function updateRowSubtotal(row) {
        const cell = row.querySelector('.line-subtotal');
        if (!cell) return;
        const subtotal = rowSubtotal(row);
        cell.textContent = subtotal > 0 ? formatMoney(subtotal) : '—';
    }

    function getRows() {
        return Array.from(body.querySelectorAll('.line-item-row'));
    }

    function calculateTotal() {
        let total = 0;
        getRows().forEach(function (row) {
            total += rowSubtotal(row);
        });

        if (saleTotalEl) {
            saleTotalEl.textContent = formatMoney(total);
        }

        updatePaymentSummary(total);
        toggleEmptyState();
        return total;
    }

    function updatePaymentSummary(total) {
        if (!paidAmount) return;

        if (!paidAmountTouched && total > 0) {
            paidAmount.value = total.toFixed(2);
        }

        const paid = parseFloat(paidAmount.value || '0');
        const due = Math.max(total - paid, 0);

        if (dueAmountEl) {
            dueAmountEl.textContent = formatMoney(due);
        }

        if (paymentStatusEl) {
            const tr = window.t || function (k) { return k; };
            let statusKey = 'status.paid';
            let badge = 'bg-success';
            if (due > 0 && paid > 0) {
                statusKey = 'status.partially_paid';
                badge = 'bg-warning text-dark';
            } else if (due > 0) {
                statusKey = 'status.due';
                badge = 'bg-danger';
            }
            paymentStatusEl.textContent = tr(statusKey);
            paymentStatusEl.className = 'badge ' + badge;
            paymentStatusEl.setAttribute('data-i18n', statusKey);
        }

        if (paid > total) {
            paidAmount.setCustomValidity((window.t || function (k) { return k; })('sales.paid_exceeds_total'));
        } else if (due > 0 && customerSelect && String(customerSelect.value) === String(config.walkinCustomerId)) {
            paidAmount.setCustomValidity((window.t || function (k) { return k; })('sales.due_needs_customer'));
        } else {
            paidAmount.setCustomValidity('');
        }
    }

    function toggleEmptyState() {
        const hasRows = getRows().length > 0;
        if (emptyCartMessage) {
            emptyCartMessage.classList.toggle('d-none', hasRows);
        }
        if (completeBtn) {
            completeBtn.disabled = !hasRows;
        }
    }

    function findRowByProductId(productId) {
        return getRows().find(function (row) {
            return row.dataset.productId === String(productId);
        });
    }

    function bindRow(row) {
        const qtyInput = row.querySelector('.quantity-input');
        const priceInput = row.querySelector('.price-input');
        const discountInput = row.querySelector('.discount-input');
        const removeBtn = row.querySelector('.remove-line');
        const stock = parseInt(row.dataset.stock || '0', 10);

        function onLineChange() {
            if (qtyInput && stock > 0) {
                qtyInput.max = stock;
            }
            updateRowSubtotal(row);
            calculateTotal();
        }

        if (qtyInput) qtyInput.addEventListener('input', onLineChange);
        if (priceInput) priceInput.addEventListener('input', onLineChange);
        if (discountInput) discountInput.addEventListener('input', onLineChange);

        if (removeBtn) {
            removeBtn.addEventListener('click', function () {
                row.remove();
                calculateTotal();
            });
        }

        updateRowSubtotal(row);
    }

    function addProductToCart(product) {
        const existingRow = findRowByProductId(product.id);
        if (existingRow) {
            const qtyInput = existingRow.querySelector('.quantity-input');
            const currentQty = parseInt(qtyInput.value || '1', 10);
            const maxStock = parseInt(existingRow.dataset.stock || '0', 10);
            if (currentQty < maxStock) {
                qtyInput.value = currentQty + 1;
                qtyInput.dispatchEvent(new Event('input'));
            }
            return;
        }

        const clone = template.content.cloneNode(true);
        const row = clone.querySelector('.line-item-row');
        row.dataset.productId = String(product.id);
        row.dataset.stock = String(product.stock || 0);

        row.querySelector('.product-id-input').value = product.id;
        row.querySelector('.product-name-label').textContent = product.name;

        const metaParts = [];
        if (product.sku) metaParts.push('SKU: ' + product.sku);
        if (product.barcode) metaParts.push('Barcode: ' + product.barcode);
        metaParts.push('Stock: ' + (product.stock || 0));
        row.querySelector('.product-meta-label').textContent = metaParts.join(' · ');

        const priceInput = row.querySelector('.price-input');
        priceInput.value = parseFloat(product.market_price || 0).toFixed(2);

        const qtyInput = row.querySelector('.quantity-input');
        qtyInput.max = product.stock || 1;

        body.appendChild(clone);
        bindRow(row);
        calculateTotal();
    }

    function hideSearchResults() {
        if (searchResults) {
            searchResults.classList.add('d-none');
            searchResults.innerHTML = '';
        }
    }

    function renderSearchResults(products) {
        if (!searchResults) return;
        searchResults.innerHTML = '';

        if (!products.length) {
            const empty = document.createElement('div');
            empty.className = 'list-group-item text-muted';
            empty.setAttribute('data-i18n', 'sales.no_products_found');
            empty.textContent = (window.t || function (k) { return k; })('sales.no_products_found');
            searchResults.appendChild(empty);
            searchResults.classList.remove('d-none');
            return;
        }

        products.forEach(function (product) {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'list-group-item list-group-item-action';
            const meta = [];
            if (product.sku) meta.push('SKU: ' + product.sku);
            if (product.barcode) meta.push('Barcode: ' + product.barcode);
            button.innerHTML =
                '<div class="fw-semibold">' + product.name + '</div>' +
                '<div class="small text-muted">' +
                meta.join(' · ') +
                (meta.length ? ' · ' : '') +
                'Stock: ' + product.stock +
                ' · Price: ৳' + parseFloat(product.market_price).toFixed(2) +
                '</div>';
            button.addEventListener('click', function () {
                addProductToCart(product);
                if (searchInput) {
                    searchInput.value = '';
                }
                hideSearchResults();
            });
            searchResults.appendChild(button);
        });

        searchResults.classList.remove('d-none');
    }

    function searchProducts(query) {
        if (!config.searchUrl) return;
        fetch(config.searchUrl + '?q=' + encodeURIComponent(query), {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
            .then(function (response) { return response.json(); })
            .then(renderSearchResults)
            .catch(function () {
                hideSearchResults();
            });
    }

    if (searchInput) {
        searchInput.addEventListener('input', function () {
            const query = searchInput.value.trim();
            clearTimeout(searchTimer);
            if (query.length < 1) {
                hideSearchResults();
                return;
            }
            searchTimer = setTimeout(function () {
                searchProducts(query);
            }, 200);
        });

        searchInput.addEventListener('keydown', function (event) {
            if (event.key === 'Escape') {
                hideSearchResults();
            }
        });
    }

    document.addEventListener('click', function (event) {
        if (!searchResults || !searchInput) return;
        if (!searchResults.contains(event.target) && event.target !== searchInput) {
            hideSearchResults();
        }
    });

    if (paidAmount) {
        paidAmount.addEventListener('input', function () {
            paidAmountTouched = true;
            calculateTotal();
        });
    }

    if (customerSelect) {
        customerSelect.addEventListener('change', function () {
            calculateTotal();
        });
    }

    if (paymentMethod) {
        paymentMethod.addEventListener('change', calculateTotal);
    }

    if (saleForm) {
        saleForm.addEventListener('submit', function (event) {
            if (!getRows().length) {
                event.preventDefault();
                alert((window.t || function (k) { return k; })('sales.add_product_alert'));
                return;
            }
            if (!saleForm.reportValidity()) {
                event.preventDefault();
            }
        });
    }

    toggleEmptyState();
    calculateTotal();
})();
