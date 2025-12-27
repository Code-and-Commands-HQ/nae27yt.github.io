const firebaseConfig = {
  apiKey: "AIzaSyA...yourKeyHere...",
  authDomain: "ghws-11a69.firebaseapp.com",
  projectId: "ghws-11a69",
  storageBucket: "ghws-11a69.appspot.com",
  messagingSenderId: "825268332046",
  appId: "1:825268332046:web:b4ef681b738b8fec0a36f"
};

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();


auth.onAuthStateChanged(user => {
    if (!user) window.location.href = "index.html";
});

function logout() {
    auth.signOut();
}
