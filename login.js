const firebaseConfig = {
    apiKey: "YOUR_KEY",
    authDomain: "YOUR_PROJECT.firebaseapp.com",
    projectId: "YOUR_PROJECT",
    storageBucket: "YOUR_PROJECT.appspot.com",
    messagingSenderId: "YOUR_ID",
    appId: "YOUR_APP_ID"
};

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();

document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const errorMsg = document.getElementById("errorMsg");

    try {
        await auth.signInWithEmailAndPassword(email, password);

        document.getElementById("loginBtn").innerText = "Logging in...";
        document.getElementById("loginBtn").style.opacity = "0.7";

        setTimeout(() => {
            window.location.href = "dashboard.html";
        }, 800);

    } catch (err) {
        errorMsg.innerText = err.message;
        errorMsg.style.opacity = "1";
    }
});
