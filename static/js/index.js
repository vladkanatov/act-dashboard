let signup = document.querySelector(".signup");
let login = document.querySelector(".login");
let slider = document.querySelector(".slider");
let formSection = document.querySelector(".form-section");

let signupButton = document.querySelector(".signup-box .clkbtn");
let loginButton = document.querySelector(".login-box .clkbtn");

API_URL = "https://45.91.238.43/";

signup.addEventListener("click", () => {
    slider.classList.add("moveslider");
    formSection.classList.add("form-section-move");
});

login.addEventListener("click", () => {
    slider.classList.remove("moveslider");
    formSection.classList.remove("form-section-move");
});

signupButton.addEventListener("click", async () => {
    const username = document.querySelector(".signup-box .username").value;
    const password = document.querySelector(".signup-box .password").value;
    const confirmPassword = document.querySelector(".signup-box .password:nth-of-type(2)").value;

    if (password !== confirmPassword) {
        alert("Passwords do not match!");
        return;
    }

    try {
        const response = await fetch(`${API_URL}/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ username, password }),
        });

        if (response.ok) {
            const data = await response.json();
            alert(data.message);
        } else {
            const error = await response.json();
            alert(error.detail);
        }
    } catch (error) {
        alert("An error occurred during registration.");
        console.error(error);
    }
});

// Авторизация пользователя
loginButton.addEventListener("click", async () => {
    const username = document.querySelector(".login-box .username").value;
    const password = document.querySelector(".login-box .password").value;

    try {
        const response = await fetch(`${API_URL}/token`, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: new URLSearchParams({ username, password }),
        });

        if (response.ok) {
            const data = await response.json();
            // Сохранение токена в localStorage
            localStorage.setItem("access_token", data.access_token);
            // Перенаправление на главную страницу с токеном
            // window.location.href = `/?token=${data.access_token}`;
            window.location.href = `/?token=${data.access_token}`;
        } else {
            const error = await response.json();
            alert(error.detail);
        }
    } catch (error) {
        alert("An error occurred during login.");
        console.error(error);
    }
});
