import { useState } from 'react';
import { useExtractions, useReviewExtraction } from '@/hooks/use-api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { PageLoader } from '@/components/ui/Spinner';
import { Database, CheckCircle, XCircle, Eye } from 'lucide-react';
import { formatDate } from '@/lib/utils';

export default function ExtractionPage() {
  const [page, setPage] = useState(1);
  const { data: extractions, isLoading } = useExtractions(page);
  const review = useReviewExtraction();
  const [viewingId, setViewingId] = useState<string | null>(null);

  if (isLoading) return <PageLoader />;

  const list = extractions || [];

  const handleReview = (id: string, approved: boolean) => {
    review.mutate({ id, data: { reviewed: true, approved } });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Data Extraction</h1>
        <p className="text-gray-500">Review and manage extracted call data</p>
      </div>

      {list.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Database size={48} className="mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold mb-2">No extractions yet</h3>
            <p className="text-gray-500">Extracted data from calls will appear here.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {list.map((item: any) => (
            <Card key={item.id} className="hover:shadow-sm transition-shadow">
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <Database size={18} className="text-purple-500" />
                    <div>
                      <p className="font-semibold text-sm">Call: {item.call_id?.slice(0, 8)}...</p>
                      <p className="text-xs text-gray-400">
                        {item.created_at && formatDate(item.created_at)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {item.confidence_score != null && (
                      <Badge variant={item.confidence_score > 0.7 ? 'success' : 'warning'}>
                        {Math.round(item.confidence_score * 100)}% confidence
                      </Badge>
                    )}
                    <Badge variant={item.reviewed ? 'success' : 'outline'}>
                      {item.reviewed ? 'Reviewed' : 'Pending Review'}
                    </Badge>
                  </div>
                </div>

                {/* Extracted data preview */}
                {item.extracted_data && (
                  <div className="mt-2">
                    {viewingId === item.id ? (
                      <pre className="bg-gray-50 rounded-lg p-4 text-xs overflow-x-auto">
                        {JSON.stringify(item.extracted_data, null, 2)}
                      </pre>
                    ) : (
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(item.extracted_data)
                          .slice(0, 4)
                          .map(([key, value]) => (
                            <span key={key} className="text-sm bg-gray-50 rounded px-2 py-1">
                              <span className="text-gray-500">{key}:</span>{' '}
                              <span className="font-medium">{String(value)}</span>
                            </span>
                          ))}
                        {Object.keys(item.extracted_data).length > 4 && (
                          <span className="text-sm text-gray-400">
                            +{Object.keys(item.extracted_data).length - 4} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center gap-2 mt-3 pt-3 border-t">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setViewingId(viewingId === item.id ? null : item.id)}
                  >
                    <Eye size={14} className="mr-1" />
                    {viewingId === item.id ? 'Collapse' : 'View Full Data'}
                  </Button>
                  {!item.reviewed && (
                    <>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleReview(item.id, true)}
                        className="text-green-600"
                      >
                        <CheckCircle size={14} className="mr-1" /> Approve
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleReview(item.id, false)}
                        className="text-red-600"
                      >
                        <XCircle size={14} className="mr-1" /> Reject
                      </Button>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {list.length >= 20 && (
        <div className="flex justify-center gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</Button>
          <span className="flex items-center px-3 text-sm text-gray-500">Page {page}</span>
          <Button variant="outline" size="sm" onClick={() => setPage(page + 1)}>Next</Button>
        </div>
      )}
    </div>
  );
}
