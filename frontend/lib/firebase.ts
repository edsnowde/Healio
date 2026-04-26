import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {

  apiKey: "AIzaSyDa3WlZhQkG5NuMUas9VAKK5BNGSjRoNvU",

  authDomain: "healio-494416.firebaseapp.com",

  projectId: "healio-494416",

  storageBucket: "healio-494416.firebasestorage.app",

  messagingSenderId: "322299516577",

  appId: "1:322299516577:web:04905b77aa395e184f82e0"

};

const app = initializeApp(firebaseConfig);

export const db = getFirestore(app);