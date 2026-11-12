/**
 * CLARIO PayPal Sandbox & Subscription Controller
 */

document.addEventListener('DOMContentLoaded', () => {
    initPayPalButton();
    initSimulatedSandboxButton();
});

function initPayPalButton() {
    const container = document.getElementById('paypal-button-container');
    if (!container || !window.paypal) return;

    try {
        paypal.Buttons({
            createOrder: function(data, actions) {
                return fetch('/api/paypal/create-order', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ plan_name: 'PRO' })
                })
                .then(res => res.json())
                .then(orderData => {
                    if (orderData.success && orderData.orderID) {
                        return orderData.orderID;
                    }
                    throw new Error(orderData.error || 'Failed to create PayPal order');
                });
            },
            onApprove: function(data, actions) {
                if (window.showToast) showToast('Verifying payment server-side...', 'info');

                return fetch('/api/paypal/capture-order', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ orderID: data.orderID })
                })
                .then(res => res.json())
                .then(captureData => {
                    if (captureData.success) {
                        if (window.showToast) showToast('Payment verified! Clario Pro Activated 🚀', 'success');
                        setTimeout(() => window.location.reload(), 1200);
                    } else {
                        if (window.showToast) showToast(captureData.error || 'Capture verification failed', 'danger');
                    }
                })
                .catch(err => {
                    if (window.showToast) showToast('Error during payment capture verification', 'danger');
                });
            },
            onError: function(err) {
                console.error('PayPal Buttons Error:', err);
                if (window.showToast) showToast('PayPal Sandbox window error or cancelled', 'warning');
            }
        }).render('#paypal-button-container');
    } catch (e) {
        console.warn('PayPal JS SDK render fallback:', e);
    }
}

function initSimulatedSandboxButton() {
    const simBtn = document.getElementById('sandboxSimulateUpgradeBtn');
    if (!simBtn) return;

    simBtn.addEventListener('click', () => {
        simBtn.disabled = true;
        simBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Verifying Sandbox Order...`;

        // 1. Create order
        fetch('/api/paypal/create-order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ plan_name: 'PRO' })
        })
        .then(res => res.json())
        .then(orderData => {
            const orderId = orderData.orderID;
            // 2. Capture and verify order
            return fetch('/api/paypal/capture-order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ orderID: orderId })
            });
        })
        .then(res => res.json())
        .then(captureData => {
            if (captureData.success) {
                if (window.showToast) showToast('PayPal Sandbox Payment verified! Clario Pro Activated! 🚀', 'success');
                setTimeout(() => window.location.reload(), 1000);
            } else {
                simBtn.disabled = false;
                simBtn.innerHTML = `Instant Sandbox Verification Test (One-Click)`;
                if (window.showToast) showToast(captureData.error || 'Verification failed', 'danger');
            }
        })
        .catch(err => {
            simBtn.disabled = false;
            simBtn.innerHTML = `Instant Sandbox Verification Test (One-Click)`;
            if (window.showToast) showToast('Sandbox network error', 'danger');
        });
    });
}
