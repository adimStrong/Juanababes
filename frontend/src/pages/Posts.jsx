import { useState, useEffect } from 'react';
import { getPosts } from '../services/api';

export default function Posts() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState({ post_type: '' });

  useEffect(() => {
    async function fetchPosts() {
      setLoading(true);
      try {
        const params = { page };
        if (filter.post_type) params.post_type = filter.post_type;
        const data = await getPosts(params);
        setPosts(data.results || data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchPosts();
  }, [page, filter]);

  const formatDate = (date) => {
    if (!date) return 'N/A';
    return new Date(date).toLocaleDateString();
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Posts</h1>
        <select
          className="border rounded-lg px-4 py-2"
          value={filter.post_type}
          onChange={(e) => setFilter({ post_type: e.target.value })}
        >
          <option value="">All Types</option>
          <option value="Photos">Photos</option>
          <option value="Videos">Videos</option>
          <option value="Reels">Reels</option>
          <option value="Live">Live</option>
          <option value="Text">Text</option>
        </select>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left font-medium text-gray-500">Title</th>
                <th className="px-6 py-3 text-left font-medium text-gray-500">Type</th>
                <th className="px-6 py-3 text-left font-medium text-gray-500">Date</th>
                <th className="px-6 py-3 text-right font-medium text-gray-500">Reactions</th>
                <th className="px-6 py-3 text-right font-medium text-gray-500">Views</th>
                <th className="px-6 py-3 text-right font-medium text-gray-500">Engagement</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {posts.map((post) => (
                <tr key={post.post_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 max-w-xs">
                    <a
                      href={post.permalink}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-600 hover:underline truncate block"
                    >
                      {post.title?.slice(0, 50) || 'Untitled'}
                    </a>
                  </td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-1 bg-gray-100 rounded text-xs">
                      {post.post_type || 'Unknown'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-500">
                    {formatDate(post.publish_time)}
                  </td>
                  <td className="px-6 py-4 text-right">
                    {post.reactions?.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-right">
                    {post.views?.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-right font-semibold">
                    {post.engagement?.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="flex justify-center gap-2">
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page === 1}
          className="px-4 py-2 border rounded-lg disabled:opacity-50"
        >
          Previous
        </button>
        <span className="px-4 py-2">Page {page}</span>
        <button
          onClick={() => setPage((p) => p + 1)}
          className="px-4 py-2 border rounded-lg"
        >
          Next
        </button>
      </div>
    </div>
  );
}
