import { ContentForm } from '@/components/contents/ContentForm';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

export default function NewContentPage() {
  return (
    <ProtectedRoute>
      <ContentForm mode="create" />
    </ProtectedRoute>
  );
}
