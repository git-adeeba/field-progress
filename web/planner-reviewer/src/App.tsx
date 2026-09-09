import {
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import AppLayout
  from "./layouts/AppLayout";

import ProtectedRoute
  from "./components/ProtectedRoute";

import Login
  from "./pages/Login";

import Dashboard
  from "./pages/Dashboard";

import Schedule
  from "./pages/Schedule";

import FieldTwin
  from "./pages/FieldTwin";

import ReviewQueue
  from "./pages/ReviewQueue";

import Exceptions
  from "./pages/Exceptions";

import AuditTrail
  from "./pages/AuditTrail";


export default function App() {
  return (
    <Routes>

      <Route
        path="/login"
        element={<Login />}
      />


      <Route
        element={<ProtectedRoute />}
      >

        <Route
          element={<AppLayout />}
        >

          <Route
            index
            element={
              <Navigate
                to="/dashboard"
                replace
              />
            }
          />


          <Route
            path="/dashboard"
            element={<Dashboard />}
          />

          <Route
            path="/schedule"
            element={<Schedule />}
          />

          <Route
            path="/field-twin"
            element={<FieldTwin />}
          />

          <Route
            path="/review-queue"
            element={<ReviewQueue />}
          />

          <Route
            path="/exceptions"
            element={<Exceptions />}
          />

          <Route
            path="/audit-trail"
            element={<AuditTrail />}
          />

        </Route>

      </Route>


      <Route
        path="*"
        element={
          <Navigate
            to="/login"
            replace
          />
        }
      />

    </Routes>
  );
}