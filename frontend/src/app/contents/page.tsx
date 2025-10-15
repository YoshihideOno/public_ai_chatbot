import { ContentsList } from '@/components/contents/ContentsList';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

export default function ContentsPage() {
  return (
    <ProtectedRoute>
      <ContentsList />
    </ProtectedRoute>
  );
}
