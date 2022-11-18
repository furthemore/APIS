async function formatError(response) {
    try {
        const r = await response.json();
        return r.reason;
    } catch (e) {
        return "Unknown"
    }
}

function showAlert(html) {
    const alertDiv = document.getElementById('alert-bar');
    alertDiv.innerHTML = html;
    alertDiv.classList.remove('alert-hidden');
}

function hideAlert() {
    const alertDiv = document.getElementById('alert-bar');
    alertDiv.classList.add('alert-hidden');
}
