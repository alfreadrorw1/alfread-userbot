// firebase-config.js
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyCTbLlKjUKI9SMVgnNgaqj9ivScgxoxynI",
  authDomain: "games-592c5.firebaseapp.com",
  databaseURL: "https://games-592c5-default-rtdb.firebaseio.com",
  projectId: "games-592c5",
  storageBucket: "games-592c5.firebasestorage.app",
  messagingSenderId: "103017684838",
  appId: "1:103017684838:web:86d5651cd44d715bc132a7",
  measurementId: "G-LQE1MMV6TY"
};
// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const db = firebase.firestore();