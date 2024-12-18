import React, { useState, useEffect } from 'react';
import { getAccounts, addAccount, deleteAccount } from '../api';

function Accounts({ token }) {
  const [accounts, setAccounts] = useState([]);
  const [newAccount, setNewAccount] = useState('');

  useEffect(() => {
    const fetchAccounts = async () => {
      const data = await getAccounts(token);
      setAccounts(data);
    };
    fetchAccounts();
  }, [token]);

  const handleAdd = async () => {
    await addAccount(token, newAccount);
    setNewAccount('');
    const data = await getAccounts(token);
    setAccounts(data);
  };

  const handleDelete = async (id) => {
    await deleteAccount(token, id);
    const data = await getAccounts(token);
    setAccounts(data);
  };

  return (
    <div>
      <h2>Instagram Accounts</h2>
      <ul>
        {accounts.map((account) => (
          <li key={account.id}>
            {account.username}
            <button onClick={() => handleDelete(account.id)}>Delete</button>
          </li>
        ))}
      </ul>
      <input
        type="text"
        placeholder="Add Account"
        value={newAccount}
        onChange={(e) => setNewAccount(e.target.value)}
      />
      <button onClick={handleAdd}>Add</button>
    </div>
  );
}

export default Accounts;
