import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './hooks/useAuth'
import { ProtectedRoute } from './components/layout/ProtectedRoute'
import { AppLayout } from './components/layout/AppLayout'
import { Login } from './pages/Login'
import { Dashboard } from './pages/Dashboard'
import { Cases } from './pages/Cases'
import { Evidence } from './pages/Evidence'
import { Timeline } from './pages/Timeline'
import { ParseErrors } from './pages/ParseErrors'
import { Reports } from './pages/Reports'
import { Scenarios } from './pages/Scenarios'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/cases" element={<Cases />} />
            <Route path="/evidence" element={<Evidence />} />
            <Route path="/timeline" element={<Timeline />} />
            <Route path="/parse-errors" element={<ParseErrors />} />
            <Route path="/scenarios" element={<Scenarios />} />
            <Route path="/reports" element={<Reports />} />
          </Route>
        </Route>
      </Routes>
    </AuthProvider>
  )
}
