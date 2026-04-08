/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { EventExplorer } from './pages/EventExplorer';
import { EventDetails } from './pages/EventDetails';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<EventExplorer />} />
        <Route path="/event/:id" element={<EventDetails />} />
      </Routes>
    </BrowserRouter>
  );
}
