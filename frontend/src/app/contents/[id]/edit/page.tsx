import { ContentForm } from '@/components/contents/ContentForm';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

interface EditContentPageProps {
  params: {
    id: string;
  };
}

export default function EditContentPage({ params }: EditContentPageProps) {
  return (
    <ProtectedRoute>
      <ContentForm contentId={params.id} mode="edit" />
    </ProtectedRoute>
  );
}
