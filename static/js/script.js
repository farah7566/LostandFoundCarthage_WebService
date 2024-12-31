document.addEventListener("DOMContentLoaded", function () {
    // Initial form view
    toggleForms('register');

    // Register form submission
    const registerForm = document.getElementById('register');
    if (registerForm) {
        registerForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const role = document.getElementById('role').value; // Get the role from the form

            fetch('/api/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password, role }),
            })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    if (data.message === "User registered successfully") {
                        // Successfully registered, now proceed to the login form
                        toggleForms('login'); // Show the login form
                    }
                })
                .catch(err => console.error('Error:', err));
        });
    }

    // Login form submission
    const loginForm = document.getElementById('login');
    if (loginForm) {
        loginForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const username = document.getElementById('login-username').value;
            const password = document.getElementById('login-password').value;

            fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password }),
            })
                .then(response => response.json())
                .then(data => {
                    if (data.access_token) {
                        alert('Login successful');
                        localStorage.setItem('access_token', data.access_token);
                        localStorage.setItem('role', data.role); // Save the role in localStorage

                         // Redirect based on the user's role
                    if (data.role === 'traveler' || data.role === 'agent') {
                        // Show the logged-in section with relevant forms
                        toggleForms('logged-in');
                    }
                    } else {
                        alert(data.message);
                    }
                })
                .catch(err => console.error('Error:', err));
        });
    }

    // Search functionality
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function (event) {
            event.preventDefault(); // Prevent the form from submitting normally

            const searchQuery = document.getElementById('searchInput').value.trim();
            if (!searchQuery) {
                alert('Please enter a description to search.');
                return;
            }

            fetch(`/search?description=${encodeURIComponent(searchQuery)}`)
                .then(response => response.json())
                .then(data => {
                    const resultsDiv = document.getElementById('results');
                    resultsDiv.innerHTML = ''; // Clear previous results

                    if (data && data.traveler_items && Array.isArray(data.traveler_items)) {
                        const travelerItems = data.traveler_items.filter(item =>
                            item.description.toLowerCase().includes(searchQuery.toLowerCase())
                        );

                        if (travelerItems.length > 0) {
                            travelerItems.forEach(item => {
                                const itemDiv = document.createElement('div');
                                itemDiv.innerHTML = `<strong>${item.item_name}</strong>: ${item.description}`;
                                resultsDiv.appendChild(itemDiv);
                            });
                        } else {
                            resultsDiv.innerHTML = '<p>No results found.</p>';
                        }
                    } else {
                        resultsDiv.innerHTML = '<p>No results found or unexpected data format.</p>';
                        console.error('Unexpected data format:', data);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('results').innerHTML = '<p>An error occurred. Check the console for details.</p>';
                });
        });
    }

    // Add item form submission
    const addItemForm = document.getElementById('add-item');
    if (addItemForm) {
        addItemForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const itemName = document.getElementById('item-name').value;
            const description = document.getElementById('description').value;
            const locationLost = document.getElementById('location-lost').value;
            const contactInfo = document.getElementById('contact-info').value;
            const reporterType = document.getElementById('reporter-type').value;
            const status = document.getElementById('status').value;
            const claimed = document.getElementById('claimed').value; // Default is false
            const claimedBy = document.getElementById('claimed-by').value; // Empty if not claimed

            if (!itemName || !description || !locationLost || !contactInfo || !reporterType || !status) {
                alert("Please fill in all the fields");
                return;
            }

            const url = reporterType === 'traveler' ? '/api/lost-items/report-by-traveler' : '/api/lost-items/report-by-agent';

            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                },
                body: JSON.stringify({
                    item_name: itemName,
                    description: description,
                    location_lost: locationLost,
                    contact_info: contactInfo,
                    claimed: claimed === 'true', // Convert to boolean
                    claimed_by: claimedBy, // Empty if not claimed
                    status: status, // Lost or Claimed
                    traveler_name: reporterType === 'traveler' ? 'Traveler Name' : undefined,
                }),
            })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    if (data.message === 'Lost item reported by traveler' || data.message === 'Lost item reported by airport agent') {
                        addItemForm.reset();
                    }
                })
                .catch(err => console.error('Error:', err));
        });
    }

    // Fetch lost items
    fetchLostItems();

    function fetchLostItems() {
        fetch('/api/lost-items')
            .then(response => response.json())
            .then(data => {
                const tableBody = document.querySelector('#lost-items-table tbody');
                tableBody.innerHTML = ''; // Clear existing table rows

                data.forEach(item => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${item.item_name}</td>
                        <td>${item.description}</td>
                        <td>${item.location_lost}</td>
                        <td>${item.contact_info}</td>
                        <td>${item.reporter_type}</td>
                        <td>${item.status}</td>
                    `;
                    tableBody.appendChild(row);
                });
            })
            .catch(error => console.error('Error fetching lost items:', error));
    }
});

// Toggle between the forms (register, login, and logged-in sections)
function toggleForms(form) {
    const forms = document.querySelectorAll('.form-container');
    forms.forEach(f => f.style.display = 'none');

    if (form === 'register') {
        document.getElementById('register-form').style.display = 'block';
    } else if (form === 'login') {
        document.getElementById('login-form').style.display = 'block';
    } else if (form === 'logged-in') {
        document.getElementById('logged-in-section').style.display = 'block';
    }
}