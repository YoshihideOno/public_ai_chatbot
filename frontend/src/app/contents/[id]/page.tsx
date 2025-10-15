import { ContentForm } from '@/components/contents/ContentForm';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

interface ContentDetailPageProps {
  params: {
    id: string;
  };
}

export default function ContentDetailPage({ params }: ContentDetailPageProps) {
  return (
    <ProtectedRoute>
      <ContentForm contentId={params.id} mode="view" />
    </ProtectedRoute>
  );
}
