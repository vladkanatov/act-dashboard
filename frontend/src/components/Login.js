// import React, { useState } from 'react';
// import { loginUser } from '../api';

// function Login({ setToken }) {
//   const [username, setUsername] = useState('');
//   const [password, setPassword] = useState('');

//   const handleSubmit = (e) => {
//     e.preventDefault();
//     handleLogin();
//   };
// }

// const handleLogin = async () => {
//   try {
//       const data = await loginUser(username, password);
//       setToken(data.access_token);  // Setting the token in the parent component's state to manage authentication
//   } catch (error) {
//       console.error('Login failed', error);
//   }
//   return (
//       <form onSubmit={(e) => handleSubmit(e)}>
//       <h2>Login</h2>
//       <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
//       <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
//       <button type="submit">Login</button>
//       </form>
//   );
// }

export default Login;
