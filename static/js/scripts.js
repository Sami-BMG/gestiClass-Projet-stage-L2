
<script>
        // Function to toggle sidebar on mobile
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('active');
        }

        // Function to handle login
        function login() {
            // Simple validation (in a real application, you would validate with backend)
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            if (email && password) {
                // Hide login and show app
                document.getElementById('loginContainer').style.display = 'none';
                document.getElementById('appContainer').style.display = 'flex';
                
                // In a real app, you would set user role based on authentication
                // For demo, we're just showing the admin dashboard
            } else {
                alert('Veuillez entrer un email et un mot de passe valides.');
            }
        }

        // Function to handle logout
        function logout() {
            // Show login and hide app
            document.getElementById('loginContainer').style.display = 'flex';
            document.getElementById('appContainer').style.display = 'none';
        }

        // In a real application, you would have functions to:
        // 1. Load different dashboard based on user role
        // 2. Handle API calls for data
        // 3. Manage user sessions
    </script>
