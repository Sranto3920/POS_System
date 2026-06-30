(function () {
    const body = document.getElementById('line-items-body');
    const template = document.getElementById('line-item-template');
    const addBtn = document.getElementById('add-line-btn');

    if (!body || !template || !addBtn) return;

    function bindRow(row) {
        const productSelect = row.querySelector('.product-select');
        const costInput = row.querySelector('.cost-price-input');
        const removeBtn = row.querySelector('.remove-line');

        if (productSelect && costInput) {
            productSelect.addEventListener('change', function () {
                const option = productSelect.selectedOptions[0];
                const cost = option ? option.dataset.cost : '';
                if (cost) {
                    costInput.value = parseFloat(cost).toFixed(2);
                }
            });
        }

        if (removeBtn) {
            removeBtn.addEventListener('click', function () {
                const rows = body.querySelectorAll('.line-item-row');
                if (rows.length <= 1) return;
                row.remove();
            });
        }
    }

    function addRow() {
        const clone = template.content.cloneNode(true);
        const row = clone.querySelector('.line-item-row');
        body.appendChild(clone);
        bindRow(row);
    }

    body.querySelectorAll('.line-item-row').forEach(bindRow);
    addBtn.addEventListener('click', addRow);
})();
