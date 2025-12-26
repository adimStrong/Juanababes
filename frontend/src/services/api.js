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

export const getStats = async () => {
  if (IS_PRODUCTION) {
    const data = await loadStaticData();
    return data.stats;
  }
  return api.get('/stats/').then(res => res.data);
};

export const getDailyEngagement = async (days = 30, page = null) => {
  if (IS_PRODUCTION) {
    const data = await loadStaticData();
    return data.daily.slice(-days);
  }
  const params = new URLSearchParams({ days });
  if (page) params.append('page', page);
  return api.get(`/stats/daily/?${params}`).then(res => res.data);
};

export const getPostTypeStats = async (page = null) => {
  if (IS_PRODUCTION) {
    const data = await loadStaticData();
    return data.postTypes;
  }
  const params = page ? `?page=${page}` : '';
  return api.get(`/stats/post-types/${params}`).then(res => res.data);
};

export const getTopPosts = async (limit = 10, metric = 'engagement', page = null) => {
  if (IS_PRODUCTION) {
    const data = await loadStaticData();
    return data.topPosts.slice(0, limit);
  }
  const params = new URLSearchParams({ limit, metric });
  if (page) params.append('page', page);
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
