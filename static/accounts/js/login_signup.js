document.querySelectorAll('.toggle-password').forEach(icon => {
    icon.addEventListener('click', () => {
        const input = document.getElementById(icon.dataset.target);
        const isPassword = input.type === 'password';
        input.type = isPassword?'text':'password';

        // Doi icon
        icon.classList.toggle('bi-eye');
        icon.classList.toggle('bi-eye-slash');

    });
})

// Check password
let input = document.getElementById('id_password1');
let result = document.getElementById('result');
let timeout = null;


input.addEventListener('input', function() {
    clearTimeout(timeout)
    timeout = setTimeout(function() {

        let password = input.value.trim();

        let hasNumber = /[0-9]/.test(password); 
        let hasUpper = /[A-Z]/.test(password); 
        let hasLower = /[a-z]/.test(password); 
        let hasSpecial = /[^A-Za-z0-9]/.test(password);

        let errors = [];
        if (password.length < 8) errors.push('ít nhất 8 kí tự');
        if (!hasLower) errors.push('chữ thường');
        if (!hasUpper) errors.push('chữ hoa');
        if (!hasNumber) errors.push('Số');
        if (!hasSpecial) errors.push('kí tự đặc biệt');

        if (errors.length === 0) {
            result.innerHTML = '✅ Mật khẩu mạnh'
        } else {
            result.innerHTML = '⚠️ Mật khẩu thiếu: ' + errors.join(', ');
        }
    }, 500);
    
})
// 🔥 Chặn submit nếu yếu
form.addEventListener('submit', function(e) {
    let isValid = checkPassword();

    if (!isValid) {
        e.preventDefault();
        result.innerText = '❌ Mật khẩu chưa đủ mạnh!';
    }
});
// Query include
