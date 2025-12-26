import { useState, useEffect } from 'react';
import { getOverlaps, getPages } from '../services/api';

export default function Overlap() {
  const [overlaps, setOverlaps] = useState([]);
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [overlapData, pageData] = await Promise.all([
          getOverlaps(),
          getPages(),
        ]);
        setOverlaps(overlapData.results || overlapData);
        setPages(pageData.results || pageData);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Audience Overlap Analysis</h1>

      {pages.length < 2 ? (
        <div className="bg-yellow-50 rounded-lg p-6">
          <h3 className="font-medium text-yellow-900">Need More Pages</h3>
          <p className="text-sm text-yellow-700 mt-1">
            Audience overlap analysis requires at least 2 Facebook pages.
            Add competitor pages to compare audience overlap.
          </p>
          <pre className="mt-3 bg-yellow-100 p-2 rounded text-sm text-yellow-900">
            python audience_overlap_analyzer.py pages
          </pre>
        </div>
      ) : overlaps.length === 0 ? (
        <div className="bg-blue-50 rounded-lg p-6">
          <h3 className="font-medium text-blue-900">No Analysis Results</h3>
          <p className="text-sm text-blue-700 mt-1">
            Run the overlap analyzer to compare audience engagement patterns:
          </p>
          <pre className="mt-3 bg-blue-100 p-2 rounded text-sm text-blue-900">
            python audience_overlap_analyzer.py analyze PAGE_ID_1 PAGE_ID_2
          </pre>
        </div>
      ) : (
        <div className="space-y-4">
          {overlaps.map((overlap) => (
            <div key={overlap.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-semibold">
                    {overlap.page_1_name} vs {overlap.page_2_name}
                  </h3>
                  <p className="text-sm text-gray-500">
                    Analysis Date: {overlap.analysis_date}
                  </p>
                </div>
                <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm">
                  {overlap.analysis_method}
                </span>
              </div>

              <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Content Similarity</p>
                  <p className="text-lg font-semibold">
                    {overlap.content_similarity_score?.toFixed(1)}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Timing Correlation</p>
                  <p className="text-lg font-semibold">
                    {overlap.posting_time_correlation?.toFixed(2)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Engagement Pattern</p>
                  <p className="text-lg font-semibold">
                    {overlap.engagement_pattern_score?.toFixed(1)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Est. Overlap</p>
                  <p className="text-lg font-semibold text-indigo-600">
                    {overlap.overlap_percentage?.toFixed(1)}%
                  </p>
                </div>
              </div>

              {overlap.notes && (
                <div className="mt-4 p-3 bg-gray-50 rounded">
                  <p className="text-sm text-gray-600">{overlap.notes}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="font-medium text-gray-900">Available Pages</h3>
        <div className="mt-2 flex flex-wrap gap-2">
          {pages.map((page) => (
            <span
              key={page.page_id}
              className={`px-3 py-1 rounded-full text-sm ${
                page.is_competitor
                  ? 'bg-orange-100 text-orange-700'
                  : 'bg-indigo-100 text-indigo-700'
              }`}
            >
              {page.page_name}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
