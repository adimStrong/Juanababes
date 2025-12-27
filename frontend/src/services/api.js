import axios from 'axios';

// Use static data in production (Vercel), API in development
const IS_PRODUCTION = import.meta.env.PROD;
const API_URL = 'http://localhost:8001/api';

let staticData = null;

async function loadStaticData() {
  if (!staticData) {
    const response = await fetch('/data/analytics.json');
    staticData = await response.json();
  }
  return staticData;
}

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getStats = async (pageId = null) => {
  if (IS_PRODUCTION) {
    const data = await loadStaticData();
    // Support per-page stats filtering
    if (pageId && data.stats.byPage && data.stats.byPage[pageId]) {
      return data.stats.byPage[pageId];
    }
    return data.stats.all || data.stats;
  }
  const params = pageId ? `?page=${pageId}` : '';
  return api.get(`/stats/${params}`).then(res => res.data);
};

export const getDailyEngagement = async (days = 30, pageId = null) => {
  if (IS_PRODUCTION) {
    const data = await loadStaticData();
    // Support per-page daily filtering
    let dailyData;
    if (pageId && data.daily.byPage && data.daily.byPage[pageId]) {
      dailyData = data.daily.byPage[pageId];
    } else {
      dailyData = data.daily.all || data.daily;
    }
    return dailyData.slice(-days);
  }
  const params = new URLSearchParams({ days });
  if (pageId) params.append('page', pageId);
  return api.get(`/stats/daily/?${params}`).then(res => res.data);
};

export const getPostTypeStats = async (pageId = null) => {
  if (IS_PRODUCTION) {
    const data = await loadStaticData();
    // Support per-page post type filtering
    if (pageId && data.postTypes.byPage && data.postTypes.byPage[pageId]) {
      return data.postTypes.byPage[pageId];
    }
    return data.postTypes.all || data.postTypes;
  }
  const params = pageId ? `?page=${pageId}` : '';
  return api.get(`/stats/post-types/${params}`).then(res => res.data);
};

export const getTopPosts = async (limit = 10, metric = 'engagement', pageId = null) => {
  if (IS_PRODUCTION) {
    const data = await loadStaticData();
    // Support per-page top posts filtering
    let posts;
    if (pageId && data.topPosts.byPage && data.topPosts.byPage[pageId]) {
      posts = data.topPosts.byPage[pageId];
    } else {
      posts = data.topPosts.all || data.topPosts;
    }
    return posts.slice(0, limit);
  }
  const params = new URLSearchParams({ limit, metric });
  if (pageId) params.append('page', pageId);
  return api.get(`/stats/top-posts/?${params}`).then(res => res.data);
};

export const getPosts = (params = {}) => {
  const searchParams = new URLSearchParams(params);
  return api.get(`/posts/?${searchParams}`).then(res => res.data);
};

export const getPost = (id) => api.get(`/posts/${id}/`).then(res => res.data);

export const getPages = async () => {
  if (IS_PRODUCTION) {
    const data = await loadStaticData();
    return data.pages;
  }
  return api.get('/pages/').then(res => res.data);
};

export const getImports = () => api.get('/imports/').then(res => res.data);

export const getOverlaps = () => api.get('/overlaps/').then(res => res.data);

export const getPageComparison = async () => {
  if (IS_PRODUCTION) {
    const data = await loadStaticData();
    return data.pages;
  }
  return api.get('/stats/pages/').then(res => res.data);
};

export default api;
