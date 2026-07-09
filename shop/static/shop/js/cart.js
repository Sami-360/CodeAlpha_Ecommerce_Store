function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split(";") : [];

    for (const cookie of cookies) {
        const trimmed = cookie.trim();
        if (trimmed.startsWith(`${name}=`)) {
            return decodeURIComponent(trimmed.substring(name.length + 1));
        }
    }

    return "";
}

function formatMoney(value) {
    const number = Number.parseFloat(value || 0);
    return `Rs. ${number.toFixed(2)}`;
}

function showCartMessage(message, isError = false) {
    const existing = document.querySelector(".cart-toast");
    if (existing) {
        existing.remove();
    }

    const toast = document.createElement("div");
    toast.className = `cart-toast ${isError ? "cart-toast-error" : ""}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    window.setTimeout(() => {
        toast.remove();
    }, 2200);
}

function updateCartBadge(count) {
    const badge = document.querySelector("#cart-count");
    if (badge) {
        badge.textContent = count;
    }
}

function updatePricingBreakdown(pricing) {
    if (!pricing) {
        return;
    }

    const fields = {
        "[data-cart-subtotal]": formatMoney(pricing.subtotal),
        "[data-cart-discount]": `- ${formatMoney(pricing.discount)}`,
        "[data-cart-tax]": formatMoney(pricing.tax),
        "[data-cart-shipping]": Number.parseFloat(pricing.shipping || 0) > 0 ? formatMoney(pricing.shipping) : "Free",
        "[data-cart-total]": formatMoney(pricing.grand_total),
    };

    for (const [selector, value] of Object.entries(fields)) {
        const element = document.querySelector(selector);
        if (element) {
            element.textContent = value;
        }
    }
}

async function postForm(url, data = {}) {
    const body = new URLSearchParams(data);
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body,
    });

    if (!response.ok) {
        throw new Error("Request failed");
    }

    return response.json();
}

function setupAddToCartButtons() {
    document.querySelectorAll(".add-to-cart-btn").forEach((button) => {
        button.addEventListener("click", async () => {
            const quantitySelector = button.dataset.quantityInput;
            const quantityInput = quantitySelector ? document.querySelector(quantitySelector) : null;
            const quantity = quantityInput ? quantityInput.value : 1;

            try {
                button.disabled = true;
                const data = await postForm(button.dataset.addToCartUrl, { quantity });
                updateCartBadge(data.cart_count);
                showCartMessage("Added to cart");
            } catch (error) {
                showCartMessage("Please log in to add items to your cart", true);
            } finally {
                button.disabled = false;
            }
        });
    });
}

function setupQuantityControls() {
    document.querySelectorAll("[data-cart-row]").forEach((row) => {
        const input = row.querySelector(".cart-quantity-input");
        const subtotal = row.querySelector("[data-item-total]");
        const total = document.querySelector("[data-cart-total]");

        row.querySelectorAll(".cart-quantity-btn").forEach((button) => {
            button.addEventListener("click", async () => {
                const current = Number.parseInt(input.value || "1", 10);
                const next = button.dataset.action === "increment" ? current + 1 : Math.max(1, current - 1);
                input.value = next;

                try {
                    const data = await postForm(row.dataset.updateUrl, { quantity: next });
                    subtotal.textContent = formatMoney(data.item_total);
                    updatePricingBreakdown(data.pricing);
                    if (total && !data.pricing) {
                        total.textContent = formatMoney(data.cart_total);
                    }
                } catch (error) {
                    showCartMessage("Could not update cart quantity", true);
                }
            });
        });
    });
}

document.addEventListener("DOMContentLoaded", () => {
    setupAddToCartButtons();
    setupQuantityControls();
});
