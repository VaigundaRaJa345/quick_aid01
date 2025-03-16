document.addEventListener('DOMContentLoaded', function () {
    const allergiesSelect = document.getElementById('allergies_select');
    const allergiesInput = document.getElementById('allergies_input');
    const disabledSelect = document.getElementById('disabled_select');
    const disabledInput = document.getElementById('disabled_input');

    allergiesSelect.addEventListener('change', function () {
        if (this.value === 'Yes') {
            allergiesInput.style.display = 'block';
        } else {
            allergiesInput.style.display = 'none';
        }
    });

    disabledSelect.addEventListener('change', function () {
        if (this.value === 'Yes') {
            disabledInput.style.display = 'block';
        } else {
            disabledInput.style.display = 'none';
        }
    });
});