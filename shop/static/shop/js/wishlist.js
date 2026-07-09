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

function updateWishlistBadge(count) {
    const badge = document.querySelector("#wishlist-count");
    if (badge) {
        badge.textContent = count;
    }
}

function setWishlistButtonState(button, inWishlist) {
    button.classList.toggle("is-active", inWishlist);
    button.setAttribute("aria-pressed", inWishlist ? "true" : "false");

    const icon = button.querySelector("i");
    if (icon) {
        icon.classList.toggle("bi-heart-fill", inWishlist);
        icon.classList.toggle("bi-heart", !inWishlist);
    }
}

async function postWishlist(url) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "X-Requested-With": "XMLHttpRequest",
        },
    });

    if (!response.ok) {
        throw new Error("Wishlist request failed");
    }

    return response.json();
}

function removeWishlistCard(button) {
    const card = button.closest("[data-wishlist-card]");
    if (card) {
        card.remove();
    }
}

function setupWishlistButtons() {
    document.querySelectorAll(".wishlist-toggle-btn").forEach((button) => {
        button.addEventListener("click", async () => {
            try {
                button.disabled = true;
                const data = await postWishlist(button.dataset.wishlistUrl);
                setWishlistButtonState(button, data.in_wishlist);
                updateWishlistBadge(data.wishlist_count);

                if (button.dataset.removeOnToggle === "true" && !data.in_wishlist) {
                    removeWishlistCard(button);
                }

                showCartMessage(data.in_wishlist ? "Added to wishlist" : "Removed from wishlist");
            } catch (error) {
                showCartMessage("Please log in to update your wishlist", true);
            } finally {
                button.disabled = false;
            }
        });
    });
}

function setupMoveToCartButtons() {
    document.querySelectorAll(".wishlist-move-btn").forEach((button) => {
        button.addEventListener("click", async () => {
            try {
                button.disabled = true;
                const cartData = await postForm(button.dataset.addToCartUrl, { quantity: 1 });
                updateCartBadge(cartData.cart_count);

                const wishlistData = await postWishlist(button.dataset.wishlistUrl);
                updateWishlistBadge(wishlistData.wishlist_count);
                removeWishlistCard(button);
                showCartMessage("Moved to cart");
            } catch (error) {
                showCartMessage("Could not move item to cart", true);
            } finally {
                button.disabled = false;
            }
        });
    });
}

document.addEventListener("DOMContentLoaded", () => {
    setupWishlistButtons();
    setupMoveToCartButtons();
});
