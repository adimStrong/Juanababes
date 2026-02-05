import axios from 'axios';

// Use static data in production (Vercel), API in development
const IS_PRODUCTION = true; // Set to true to use static JSON files
const API_URL = 'http://localhost:8001/api/v1';

let staticData = null;

async function loadStaticData() {
  if (!staticData) {
    // Cache-bust to get fresh data
    const response = await fetch('/data/analytics-v2.json?t=' + Date.now());
    staticData = await response.json();
  }
  return staticData;
}

// Normalize date to YYYY-MM-DD format
function normalizeDate(dateStr) {
  if (!dateStr) return null;
  // If already YYYY-MM-DD format
  if (dateStr.length >= 10 && dateStr[4] === '-') {
    return dateStr.slice(0, 10);
  }
  // If MM/DD/YYYY format
  if (dateStr.includes('/')) {
    const parts = dateStr.split('/');
    if (parts.length >= 3) {
      const [month, day, year] = parts;
      return `${year.slice(0, 4)}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
    }
  }
  return dateStr.slice(0, 10);
}

// Date filter helper
function filterByDateRange(data, startDate, endDate, dateField = 'date') {
  if (!startDate && !endDate) return data;
  return data.filter(item => {
    const itemDate = item[dateField];
    if (!itemDate) return true;
    if (startDate && itemDate < startDate) return false;
    if (endDate && itemDate > endDate) return false;
    return true;
  });
}

// Merge Videos and Reels into a single category
function mergeVideoReels(postTypes) {
  if (!Array.isArray(postTypes)) return postTypes;

  const videoIdx = postTypes.findIndex(p => p.post_type === 'Videos');
  const reelIdx = postTypes.findIndex(p => p.post_type === 'Reels');

  // If both don't exist, return as-is
  if (videoIdx === -1 && reelIdx === -1) return postTypes;

  const video = videoIdx !== -1 ? postTypes[videoIdx] : { count: 0, reactions: 0, comments: 0, shares: 0, total_engagement: 0 };
  const reel = reelIdx !== -1 ? postTypes[reelIdx] : { count: 0, reactions: 0, comments: 0, shares: 0, total_engagement: 0 };

  const combined = {
    post_type: 'Videos/Reels',
    count: (video.count || 0) + (reel.count || 0),
    reactions: (video.reactions || 0) + (reel.reactions || 0),
    comments: (video.comments || 0) + (reel.comments || 0),
    shares: (video.shares || 0) + (reel.shares || 0),
    total_engagement: (video.total_engagement || 0) + (reel.total_engagement || 0),
  };
  combined.avg_engagement = combined.count > 0 ? Math.round(combined.total_engagement / combined.count) : 0;

  return postTypes
    .filter(p => p.post_type !== 'Videos' && p.post_type !== 'Reels')
    .concat(combined);
}

// Normalize post_type for individual posts
function normalizePostType(post) {
  if (post.post_type === 'Videos' || post.post_type === 'Reels') {
    return { ...post, post_type: 'Videos/Reels' };
  }
  return post;
}

// Normalize post field names for display
function normalizePostFields(p) {
  return {
    ...p,
    comments: p.comments ?? p.comments_count ?? 0,
    reactions: p.reactions ?? p.reactions_total ?? 0,
    shares: p.shares ?? p.shares_count ?? 0,
    engagement: p.engagement ?? p.total_engagement ?? 0,
    views: p.views ?? p.views_count ?? 0,
    reach: p.reach ?? p.reach_count ?? 0,
  };
}

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getStats = async (pageId = null, dateRange = {}) => {
  if (IS_PRODUCTION) {
    const data = await loadStaticData();
    const { startDate, endDate } = dateRange;

    // If date range specified, calculate stats from filtered daily data
    if (startDate || endDate) {
      let dailyData;
      if (pageId && data.daily.byPage && data.daily.byPage[pageId]) {
        dailyData = data.daily.byPage[pageId];
      } else {
        dailyData = data.daily.all || data.daily;
      }
      const filtered = filterByDateRange(dailyData, startDate, endDate);

      // Calculate totals from filtered daily data
      const totals = filtered.reduce((acc, day) => ({
        total_posts: acc.total_posts + (day.posts || 0),
        total_views: acc.total_views + (day.views || 0),
        total_reach: acc.total_reach + (day.reach || 0),
        total_engagement: acc.total_engagement + (day.engagement || 0),
        total_reactions: acc.total_reactions + (day.reactions || 0),
        total_comments: acc.total_comments + (day.comments || 0),
        total_shares: acc.total_shares + (day.shares || 0),
      }), { total_posts: 0, total_views: 0, total_reach: 0, total_engagement: 0, total_reactions: 0, total_comments: 0, total_shares: 0 });

      const postCount = totals.total_posts || 1;
      return {
        ...totals,
        avg_views: Math.round(totals.total_views / postCount),
        avg_reach: Math.round(totals.total_reach / postCount),
        avg_engagement: Math.round(totals.total_engagement / postCount),
        total_pages: data.pages?.length || 0,
        all_pages: data.pages?.length || 0,
        date_range_start: startDate || filtered[0]?.date,
        date_range_end: endDate || filtered[filtered.length - 1]?.date,
      };
    }

    // Support per-page stats filtering
    if (pageId && data.stats.byPage && data.stats.byPage[pageId]) {
      return data.stats.byPage[pageId];
    }
    return data.stats.all || data.stats;
  }
  const params = pageId ? `?page=${pageId}` : '';
  return api.get(`/stats/${params}`).then(res => res.data);
};

export const getDailyEngagement = async (days = 30, pageId = null, dateRange = {}) => {
  if (IS_PRODUCTION) {
    const data = await loadStaticData();
    const { startDate, endDate } = dateRange;

    // Support per-page daily filtering
    let dailyData;
    if (pageId && data.daily.byPage && data.daily.byPage[pageId]) {
      dailyData = data.daily.byPage[pageId];
    } else {
      dailyData = data.daily.all || data.daily;
    }

    // If date range specified, use it
    if (startDate || endDate) {
      return filterByDateRange(dailyData, startDate, endDate);
    }

    // Return all data (no T+2 filter)
    return dailyData.slice(-days);
  }
  const params = new URLSearchParams({ days });
  if (pageId) params.append('page', pageId);
  return api.get(`/stats/daily/?${params}`).then(res => res.data);
};

export const getPostTypeStats = async (pageId = null, dateRange = {}) => {
  if (IS_PRODUCTION) {
    const data = await loadStaticData();
    const { startDate, endDate } = dateRange;

    // Calculate from posts to include comments
    let posts = data.posts || [];
    if (pageId) {
      posts = posts.filter(p => p.page_id === pageId);
    }

    // Apply date filter
    if (startDate || endDate) {
      posts = posts.filter(p => {
        const postDate = normalizeDate(p.publish_time);
        if (!postDate) return true;
        if (startDate && postDate < startDate) return false;
        if (endDate && postDate > endDate) return false;
        return true;
      });
    }

    // Aggregate by post type
    const typeStats = {};
    posts.forEach(p => {
      const type = p.post_type || 'UNKNOWN';
      if (!typeStats[type]) {
        typeStats[type] = {
          post_type: type,
          count: 0,
          reactions: 0,
          comments: 0,
          shares: 0,
          total_engagement: 0,
        };
      }
      typeStats[type].count++;
      typeStats[type].reactions += p.reactions || p.reactions_total || 0;
      typeStats[type].comments += p.comments || p.comments_count || 0;
      typeStats[type].shares += p.shares || p.shares_count || 0;
      typeStats[type].total_engagement += p.engagement || p.total_engagement || 0;
    });

    // Calculate averages
    const postTypes = Object.values(typeStats).map(pt => ({
      ...pt,
      avg_engagement: pt.count > 0 ? Math.round(pt.total_engagement / pt.count) : 0,
    })).sort((a, b) => b.total_engagement - a.total_engagement);

    // Merge Videos and Reels into single category
    return mergeVideoReels(postTypes);
  }
  const params = pageId ? `?page=${pageId}` : '';
  return api.get(`/stats/post-types/${params}`).then(res => res.data);
};

export const getTopPosts = async (limit = 10, metric = 'engagement', pageId = null, dateRange = {}) => {
  if (IS_PRODUCTION) {
    const data = await loadStaticData();
    const { startDate, endDate } = dateRange;

    // If date range specified, calculate from all posts
    if (startDate || endDate) {
      let posts = (data.posts || []).map(p => normalizePostFields(normalizePostType(p)));

      // Filter by page if specified
      if (pageId) {
        posts = posts.filter(p => p.page_id === pageId);
      }

      // Apply date filter
      posts = posts.filter(p => {
        const postDate = normalizeDate(p.publish_time);
        if (!postDate) return true;
        if (startDate && postDate < startDate) return false;
        if (endDate && postDate > endDate) return false;
        return true;
      });

      // Sort by metric and return top N
      const sortKey = metric === 'engagement' ? 'engagement' : metric;
      posts.sort((a, b) => (b[sortKey] || 0) - (a[sortKey] || 0));
      return posts.slice(0, limit);
    }

    // No date range - use pre-calculated top posts
    let posts;
    if (pageId && data.topPosts.byPage && data.topPosts.byPage[pageId]) {
      posts = data.topPosts.byPage[pageId];
    } else {
      posts = data.topPosts.all || data.topPosts;
    }
    // Normalize post_type and field names
    return posts.slice(0, limit).map(p => normalizePostFields(normalizePostType(p)));
  }
  const params = new URLSearchParams({ limit, metric });
  if (pageId) params.append('page', pageId);
  return api.get(`/stats/top-posts/?${params}`).then(res => res.data);
};

export const getPosts = async (params = {}, dateRange = {}) => {
  if (IS_PRODUCTION) {
    const data = await loadStaticData();
    // Normalize post_type and field names
    let posts = (data.posts || []).map(p => normalizePostFields(normalizePostType(p)));

    // Apply date range filter
    const { startDate, endDate } = dateRange;
    if (startDate || endDate) {
      posts = posts.filter(p => {
        const postDate = normalizeDate(p.publish_time);
        if (!postDate) return true;
        if (startDate && postDate < startDate) return false;
        if (endDate && postDate > endDate) return false;
        return true;
      });
    }

    // Apply filters
    if (params.post_type) {
      posts = posts.filter(p => p.post_type === params.post_type);
    }
    if (params.page_id) {
      posts = posts.filter(p => p.page_id === params.page_id);
    }
    if (params.search) {
      const search = params.search.toLowerCase();
      posts = posts.filter(p =>
        (p.title || '').toLowerCase().includes(search) ||
        (p.page_name || '').toLowerCase().includes(search)
      );
    }

    // Pagination
    const page = parseInt(params.page || 1);
    const pageSize = 20;
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    const paginatedPosts = posts.slice(start, end);

    return {
      results: paginatedPosts,
      count: posts.length,
      next: end < posts.length ? page + 1 : null,
      previous: page > 1 ? page - 1 : null,
    };
  }
  const searchParams = new URLSearchParams(params);
  return api.get(`/posts/?${searchParams}`).then(res => res.data);
};

export const getPost = (id) => api.get(`/posts/${id}/`).then(res => res.data);

export const getPages = async (dateRange = {}) => {
  if (IS_PRODUCTION) {
    const data = await loadStaticData();
    const { startDate, endDate } = dateRange;

    // Always aggregate from posts to ensure total_comments is calculated
    let posts = (data.posts || []);

    // Apply date filter if specified
    if (startDate || endDate) {
      posts = posts.filter(p => {
        const postDate = normalizeDate(p.publish_time);
        if (!postDate) return true;
        if (startDate && postDate < startDate) return false;
        if (endDate && postDate > endDate) return false;
        return true;
      });
    }

    // Aggregate by page
    const pageStats = {};
    posts.forEach(p => {
      const pid = p.page_id;
      if (!pageStats[pid]) {
        // Get base page info from data.pages
        const basePage = (data.pages || []).find(pg => pg.page_id === pid) || {};
        pageStats[pid] = {
          page_id: pid,
          page_name: p.page_name || basePage.page_name,
          name: p.page_name || basePage.page_name,
          fan_count: basePage.fan_count || 0,
          followers_count: basePage.followers_count || 0,
          post_count: 0,
          total_views: 0,
          total_reach: 0,
          total_reactions: 0,
          total_comments: 0,
          total_shares: 0,
          total_engagement: 0,
        };
      }
      pageStats[pid].post_count++;
      pageStats[pid].total_views += p.views || p.views_count || 0;
      pageStats[pid].total_reach += p.reach || p.reach_count || 0;
      pageStats[pid].total_reactions += p.reactions || p.reactions_total || 0;
      pageStats[pid].total_comments += p.comments || p.comments_count || 0;
      pageStats[pid].total_shares += p.shares || p.shares_count || 0;
      pageStats[pid].total_engagement += p.engagement || p.total_engagement || 0;
    });

    // Calculate averages and sort by engagement
    return Object.values(pageStats)
      .map(p => ({
        ...p,
        avg_engagement: p.post_count > 0 ? Math.round(p.total_engagement / p.post_count) : 0,
        avg_reach: p.post_count > 0 ? Math.round(p.total_reach / p.post_count) : 0,
      }))
      .sort((a, b) => b.total_engagement - a.total_engagement);
  }
  return api.get('/pages/').then(res => res.data);
};

export const getImports = () => api.get('/imports/').then(res => res.data);

export const getOverlaps = async () => {
  if (IS_PRODUCTION) {
    const data = await loadStaticData();
    return data.overlaps || [];
  }
  return api.get('/overlaps/').then(res => res.data);
};

export const getDailyByPage = async (days = 60, dateRange = {}) => {
  const data = await loadStaticData();
  const { startDate, endDate } = dateRange;
  const pages = data.pages || [];
  const byPage = data.daily.byPage || {};
  let allDaily = data.daily.all || [];

  // Apply date filter if specified
  if (startDate || endDate) {
    allDaily = filterByDateRange(allDaily, startDate, endDate);
  } else {
    allDaily = allDaily.slice(-days);
  }

  // Create a map of all dates
  const dateMap = {};
  allDaily.forEach(entry => {
    dateMap[entry.date] = { date: entry.date };
  });

  // Add each page's posts to the date map
  pages.forEach(page => {
    let pageDaily = byPage[page.page_id] || [];
    // Apply date filter to page data as well
    if (startDate || endDate) {
      pageDaily = filterByDateRange(pageDaily, startDate, endDate);
    }
    pageDaily.forEach(entry => {
      if (dateMap[entry.date]) {
        // Use short page name (e.g., "Ashley" instead of "Juana Babe Ashley")
        const shortName = page.page_name.replace('Juana Babe ', '');
        dateMap[entry.date][shortName] = entry.posts;
      }
    });
  });

  // Convert to array and sort by date
  const result = Object.values(dateMap).sort((a, b) => a.date.localeCompare(b.date));

  // Get page names for the chart
  const pageNames = pages.map(p => p.page_name.replace('Juana Babe ', ''));

  return { data: result, pageNames };
};

export const getTimeSeries = async (dateRange = {}) => {
  if (IS_PRODUCTION) {
    const data = await loadStaticData();
    const { startDate, endDate } = dateRange;
    const timeSeries = data.timeSeries || {
      monthly: [],
      weekly: [],
      dayOfWeek: [],
      pageRankings: [],
      postTypePerf: [],
      insights: []
    };

    // If date range specified, filter the time series data
    if (startDate || endDate) {
      return {
        ...timeSeries,
        monthly: filterByDateRange(timeSeries.monthly || [], startDate, endDate, 'month'),
        weekly: filterByDateRange(timeSeries.weekly || [], startDate, endDate, 'week'),
      };
    }

    return timeSeries;
  }
  // For dev, calculate from daily data (simplified)
  return api.get('/stats/time-series/').then(res => res.data);
};

export const getCommentAnalysis = async () => {
  if (IS_PRODUCTION) {
    const data = await loadStaticData();
    return data.commentAnalysis || {
      summary: {},
      byPage: [],
      effectivity: {},
      topSelfCommented: []
    };
  }
  return api.get('/stats/comment-analysis/').then(res => res.data);
};

export const getPageComparison = async (dateRange = {}) => {
  if (IS_PRODUCTION) {
    const data = await loadStaticData();
    const { startDate, endDate } = dateRange;

    // Always calculate from posts to ensure data is available
    let posts = (data.posts || []);

    // Apply date filter if specified
    if (startDate || endDate) {
      posts = posts.filter(p => {
        const postDate = normalizeDate(p.publish_time);
        if (!postDate) return true;
        if (startDate && postDate < startDate) return false;
        if (endDate && postDate > endDate) return false;
        return true;
      });
    }

    // Aggregate by page
    const pageStats = {};
    const postTypesByPage = {};

    posts.forEach(p => {
      const pid = p.page_id;
      if (!pageStats[pid]) {
        // Get base page info for fan_count
        const basePage = (data.pages || []).find(pg => pg.page_id === pid) || {};
        pageStats[pid] = {
          page_id: pid,
          page_name: p.page_name,
          posts: 0,
          views: 0,
          reach: 0,
          reactions: 0,
          comments: 0,
          shares: 0,
          engagement: 0,
          fan_count: basePage.fan_count || 0,
        };
        postTypesByPage[pid] = {};
      }
      pageStats[pid].posts++;
      pageStats[pid].views += p.views_count || p.views || 0;
      pageStats[pid].reach += p.reach_count || p.reach || 0;
      pageStats[pid].reactions += p.reactions_total || p.reactions || 0;
      pageStats[pid].comments += p.comments_count || p.comments || 0;
      pageStats[pid].shares += p.shares_count || p.shares || 0;
      pageStats[pid].engagement += p.total_engagement || p.engagement || 0;

      // Track post types
      const ptype = p.post_type || 'Unknown';
      if (!postTypesByPage[pid][ptype]) {
        postTypesByPage[pid][ptype] = { type: ptype, count: 0, engagement: 0 };
      }
      postTypesByPage[pid][ptype].count++;
      postTypesByPage[pid][ptype].engagement += p.total_engagement || p.engagement || 0;
    });

    // Calculate averages, sort, and add rankings
    const totalEngagement = Object.values(pageStats).reduce((sum, p) => sum + p.engagement, 0);
    const pages = Object.values(pageStats)
      .map(p => ({
        ...p,
        avg_engagement: p.posts > 0 ? Math.round(p.engagement / p.posts) : 0,
        engagement_share: totalEngagement > 0 ? Math.round((p.engagement / totalEngagement) * 100) : 0,
      }))
      .sort((a, b) => b.engagement - a.engagement)
      .map((p, idx) => ({ ...p, rank: idx + 1 }));

    // Convert postTypesByPage to arrays and find dominant types
    const postTypesResult = {};
    const dominantTypes = {};
    Object.keys(postTypesByPage).forEach(pid => {
      const types = Object.values(postTypesByPage[pid]).sort((a, b) => b.count - a.count);
      postTypesResult[pid] = types;
      dominantTypes[pid] = types[0] || { type: 'N/A' };
    });

    return { pages, postTypesByPage: postTypesResult, dominantTypes };
  }
  return api.get('/stats/page-comparison/').then(res => res.data);
};

export const getDateBoundaries = async () => {
  if (IS_PRODUCTION) {
    const data = await loadStaticData();
    const posts = data.posts || [];
    if (posts.length === 0) return { minDate: null, maxDate: null };

    const dates = posts
      .map(p => p.publish_time?.slice(0, 10))
      .filter(d => d)
      .sort();

    return {
      minDate: dates[0],
      maxDate: dates[dates.length - 1]
    };
  }
  return { minDate: null, maxDate: null };
};

export default api;
