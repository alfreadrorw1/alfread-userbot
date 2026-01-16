// firebase-config.js
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyDBNHEbhrQBfNlcs2IJt3Fui--1-jkTv54",
  authDomain: "family100-2f913.firebaseapp.com",
  databaseURL: "https://family100-2f913-default-rtdb.firebaseio.com",
  projectId: "family100-2f913",
  storageBucket: "family100-2f913.firebasestorage.app",
  messagingSenderId: "536609229146",
  appId: "1:536609229146:web:62b2e4194de0db93f30b63",
  measurementId: "G-NCCEEZRFV1"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const db = firebase.firestore();