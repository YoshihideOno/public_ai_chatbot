import { UsersList } from '@/components/users/UsersList';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

export default function UsersPage() {
  return (
    <ProtectedRoute>
      <UsersList />
    </ProtectedRoute>
  );
}
