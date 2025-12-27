import { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, BarChart, Bar, Legend
} from 'recharts';
import StatCard from '../components/StatCard';
import { getStats, getDailyEngagement, getPostTypeStats, getTopPosts, getPageComparison } from '../services/api';

const COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6'];

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [dailyData, setDailyData] = useState([]);
  const [postTypes, setPostTypes] = useState([]);
  const [topPosts, setTopPosts] = useState([]);
  const [pageComparison, setPageComparison] = useState([]);
  const [selectedPage, setSelectedPage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [statsData, dailyData, postTypeData, topPostsData, pageData] = await Promise.all([
          getStats(selectedPage),
          getDailyEngagement(60, selectedPage),
          getPostTypeStats(selectedPage),
          getTopPosts(5, 'engagement', selectedPage),
          getPageComparison(),
        ]);
        setStats(statsData);
        setDailyData(dailyData);
        setPostTypes(postTypeData);
        setTopPosts(topPostsData);
        setPageComparison(pageData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [selectedPage]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 text-red-600 p-4 rounded-lg">
        Error loading data: {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">JuanBabes Dashboard</h1>
          <p className="text-sm text-gray-500">
            {stats?.date_range_start} - {stats?.date_range_end}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <select
            value={selectedPage || ''}
            onChange={(e) => setSelectedPage(e.target.value || null)}
            className="px-4 py-2 border border-gray-300 rounded-lg bg-white text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="">All Pages</option>
            {pageComparison.map((page) => (
              <option key={page.page_id} value={page.page_id}>
                {page.page_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Stats Cards - Row 1 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          title="Total Posts"
          value={stats?.total_posts}
          icon=""
          color="indigo"
        />
        <StatCard
          title="Total Views"
          value={stats?.total_views?.toLocaleString()}
          subtitle={`Avg: ${stats?.avg_views?.toLocaleString() || 0}/post`}
          icon=""
          color="purple"
        />
        <StatCard
          title="Total Reach"
          value={stats?.total_reach?.toLocaleString()}
          subtitle={`Avg: ${stats?.avg_reach?.toLocaleString() || 0}/post`}
          icon=""
          color="cyan"
        />
        <StatCard
          title="Total Engagement"
          value={stats?.total_engagement}
          subtitle={`Avg: ${stats?.avg_engagement?.toLocaleString()}`}
          icon=""
          color="green"
        />
        <StatCard
          title="Total PES"
          value={stats?.total_pes?.toLocaleString()}
          subtitle={`Avg: ${stats?.avg_pes?.toLocaleString()}`}
          icon=""
          color="orange"
        />
      </div>

      {/* Stats Cards - Row 2 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Reactions"
          value={stats?.total_reactions?.toLocaleString()}
          icon=""
          color="pink"
        />
        <StatCard
          title="Total Comments"
          value={stats?.total_comments?.toLocaleString()}
          icon=""
          color="blue"
        />
        <StatCard
          title="Total Shares"
          value={stats?.total_shares?.toLocaleString()}
          icon=""
          color="amber"
        />
        <StatCard
          title="Active Pages"
          value={`${stats?.total_pages || 0} / ${stats?.all_pages || stats?.total_pages || 0}`}
          subtitle="Pages with engagement data"
          icon=""
          color="teal"
        />
      </div>

      {/* Page Comparison Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Page Comparison - Total Engagement</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={pageComparison} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" fontSize={12} />
            <YAxis
              type="category"
              dataKey="page_name"
              fontSize={12}
              width={120}
              tickFormatter={(val) => val?.replace('Juana Babe ', '')}
            />
            <Tooltip
              formatter={(value, name) => [value?.toLocaleString(), name]}
            />
            <Legend />
            <Bar dataKey="total_engagement" name="Total Engagement" fill="#6366f1" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Page Stats Table */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">5 Pages Performance Summary</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[700px]">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="pb-3 font-medium whitespace-nowrap">Page</th>
                <th className="pb-3 font-medium text-right whitespace-nowrap">Posts</th>
                <th className="pb-3 font-medium text-right whitespace-nowrap">Reactions</th>
                <th className="pb-3 font-medium text-right whitespace-nowrap">Comments</th>
                <th className="pb-3 font-medium text-right whitespace-nowrap">Shares</th>
                <th className="pb-3 font-medium text-right whitespace-nowrap">Engagement</th>
                <th className="pb-3 font-medium text-right whitespace-nowrap">Avg/Post</th>
                <th className="pb-3 font-medium text-right whitespace-nowrap">Avg PES</th>
              </tr>
            </thead>
            <tbody>
              {pageComparison.map((page, index) => (
                <tr
                  key={page.page_id}
                  className={`border-b hover:bg-gray-50 ${index === 0 ? 'bg-indigo-50' : ''}`}
                >
                  <td className="py-3 font-medium whitespace-nowrap">
                    {page.page_name?.replace('Juana Babe ', '')}
                    {index === 0 && (
                      <span className="ml-2 px-2 py-0.5 bg-indigo-600 text-white text-xs rounded">
                        TOP
                      </span>
                    )}
                  </td>
                  <td className="py-3 text-right whitespace-nowrap">{page.post_count?.toLocaleString()}</td>
                  <td className="py-3 text-right whitespace-nowrap">{page.total_reactions?.toLocaleString()}</td>
                  <td className="py-3 text-right whitespace-nowrap">{page.total_comments?.toLocaleString()}</td>
                  <td className="py-3 text-right whitespace-nowrap">{page.total_shares?.toLocaleString()}</td>
                  <td className="py-3 text-right font-semibold text-indigo-600 whitespace-nowrap">
                    {page.total_engagement?.toLocaleString()}
                  </td>
                  <td className="py-3 text-right whitespace-nowrap">{page.avg_engagement?.toLocaleString()}</td>
                  <td className="py-3 text-right whitespace-nowrap">{page.avg_pes?.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Engagement Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Daily Engagement (60 days)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={dailyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(val) => val?.slice(5) || ''}
                fontSize={12}
              />
              <YAxis fontSize={12} />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="engagement"
                name="Engagement"
                stroke="#6366f1"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="pes"
                name="PES"
                stroke="#22c55e"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Post Type Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Post Type Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={postTypes}
                dataKey="count"
                nameKey="post_type"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ post_type, count }) => `${post_type}: ${count}`}
              >
                {postTypes.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Reach & Views Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Reach Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Daily Reach (60 days)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={dailyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(val) => val?.slice(5) || ''}
                fontSize={12}
              />
              <YAxis fontSize={12} tickFormatter={(val) => val >= 1000 ? `${(val/1000).toFixed(0)}k` : val} />
              <Tooltip formatter={(value) => value?.toLocaleString()} />
              <Legend />
              <Line
                type="monotone"
                dataKey="reach"
                name="Reach"
                stroke="#06b6d4"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Daily Views Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Daily Views (60 days)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={dailyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(val) => val?.slice(5) || ''}
                fontSize={12}
              />
              <YAxis fontSize={12} tickFormatter={(val) => val >= 1000 ? `${(val/1000).toFixed(0)}k` : val} />
              <Tooltip formatter={(value) => value?.toLocaleString()} />
              <Legend />
              <Line
                type="monotone"
                dataKey="views"
                name="Views"
                stroke="#8b5cf6"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Daily Content Count */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Daily Content Published (60 days)</h2>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={dailyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tickFormatter={(val) => val?.slice(5) || ''}
              fontSize={12}
            />
            <YAxis fontSize={12} allowDecimals={false} />
            <Tooltip />
            <Legend />
            <Bar dataKey="posts" name="Posts Published" fill="#6366f1" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Top Posts */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Top Performing Posts</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm table-fixed">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="pb-3 font-medium w-16">Page</th>
                <th className="pb-3 font-medium w-64">Title</th>
                <th className="pb-3 font-medium w-20">Type</th>
                <th className="pb-3 font-medium text-right w-20">Reactions</th>
                <th className="pb-3 font-medium text-right w-20">Comments</th>
                <th className="pb-3 font-medium text-right w-16">Shares</th>
                <th className="pb-3 font-medium text-right w-24">Engagement</th>
                <th className="pb-3 font-medium text-right w-20">PES</th>
              </tr>
            </thead>
            <tbody>
              {topPosts.map((post) => (
                <tr key={post.post_id} className="border-b hover:bg-gray-50">
                  <td className="py-3 text-xs text-gray-600 truncate">
                    {post.page_name?.replace('Juana Babe ', '')}
                  </td>
                  <td className="py-3 truncate">
                    <a
                      href={post.permalink}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-600 hover:underline"
                      title={post.title}
                    >
                      {post.title?.slice(0, 60) || 'Untitled'}...
                    </a>
                  </td>
                  <td className="py-3">
                    <span className="px-2 py-1 bg-gray-100 rounded text-xs">
                      {post.post_type}
                    </span>
                  </td>
                  <td className="py-3 text-right">{post.reactions?.toLocaleString()}</td>
                  <td className="py-3 text-right">{post.comments?.toLocaleString()}</td>
                  <td className="py-3 text-right">{post.shares?.toLocaleString()}</td>
                  <td className="py-3 text-right font-semibold text-indigo-600">
                    {post.engagement?.toLocaleString()}
                  </td>
                  <td className="py-3 text-right text-green-600 font-medium">
                    {post.pes?.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Post Type Performance */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Engagement by Post Type</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={postTypes}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="post_type" fontSize={12} />
            <YAxis fontSize={12} />
            <Tooltip />
            <Legend />
            <Bar dataKey="avg_engagement" name="Avg Engagement" fill="#6366f1" />
            <Bar dataKey="avg_pes" name="Avg PES" fill="#22c55e" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
