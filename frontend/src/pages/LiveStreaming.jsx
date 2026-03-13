import { useState, useEffect, useMemo } from 'react';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, ComposedChart, PieChart, Pie, Cell,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  AreaChart, Area
} from 'recharts';

// ── Constants ──
const AGENT_COLORS = { SENA: '#6366f1', ASHLEY: '#a855f7', ABI: '#f59e0b', JAM: '#22c55e' };
const PLATFORM_COLORS = { TikTok: '#00f2ea', Bigo: '#a855f7', Facebook: '#3b82f6', Other: '#6b7280' };

const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'tiktok', label: 'TikTok' },
  { id: 'bigo', label: 'Bigo' },
  { id: 'compare', label: 'Comparison' },
  { id: 'schedule', label: 'Schedule' },
  { id: 'daily', label: 'Daily' },
  { id: 'promo', label: 'Promo Codes' },
];

const fmt = (n) => {
  if (n == null || isNaN(n)) return '0';
  if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(1) + 'M';
  if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(1) + 'K';
  return n.toLocaleString();
};

const pct = (n) => (n != null ? n.toFixed(1) + '%' : '0%');

// ── Data Loading ──
let cachedData = null;
async function loadLiveData() {
  if (!cachedData) {
    const resp = await fetch('/data/analytics-v2.json?t=' + Date.now());
    cachedData = await resp.json();
  }
  return cachedData?.liveStreaming || null;
}

// ── Stat Card ──
function StatCard({ label, value, sub, color = '#6366f1' }) {
  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
      <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-bold mt-1" style={{ color }}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

// ── Custom Tooltip ──
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-gray-900 text-white text-xs rounded-lg px-3 py-2 shadow-lg">
      <p className="font-medium mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>{p.name}: {fmt(p.value)}</p>
      ))}
    </div>
  );
}

// ── Helpers for recomputing from filtered rows ──
const SUM_FIELDS = [
  'tk_views', 'tk_unique', 'tk_likes', 'tk_comments', 'tk_shares',
  'tk_gifters', 'tk_new_followers', 'bg_viewers', 'bg_engaged',
  'bg_beans', 'bg_new_fans', 'bg_gifts', 'total_engagement', 'total_reach'
];
const AVG_FIELDS = ['tk_eng_rate', 'bg_eng_rate'];

function computeTotals(rows) {
  const t = {};
  SUM_FIELDS.forEach(f => t[f] = 0);
  AVG_FIELDS.forEach(f => t[f] = 0);
  rows.forEach(r => {
    SUM_FIELDS.forEach(f => t[f] += (r[f] || 0));
    AVG_FIELDS.forEach(f => t[f] += (r[f] || 0));
  });
  if (rows.length > 0) AVG_FIELDS.forEach(f => t[f] /= rows.length);
  return t;
}

function computeAgentSummaries(rows, agents) {
  const out = {};
  agents.forEach(a => {
    const agentRows = rows.filter(r => r.agent === a);
    out[a] = computeTotals(agentRows);
  });
  return out;
}

function aggregateDailyAll(rows) {
  const byDate = {};
  rows.forEach(r => {
    if (!byDate[r.date]) byDate[r.date] = { date: r.date };
    const d = byDate[r.date];
    SUM_FIELDS.forEach(f => d[f] = (d[f] || 0) + (r[f] || 0));
  });
  return Object.values(byDate).sort((a, b) => a.date.localeCompare(b.date));
}

// ── Main Component ──
export default function LiveStreaming() {
  const [data, setData] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [agentFilter, setAgentFilter] = useState('All');

  useEffect(() => {
    loadLiveData()
      .then(d => { if (d) setData(d); else setError('No livestream data. Run fetch_livestream.py first.'); })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  // Raw data from JSON
  const raw = useMemo(() => {
    if (!data) return { agents: [], dailyAll: [], daily: [], schedule: [], promo: {} };
    return {
      agents: data.agents || ['SENA', 'ASHLEY', 'ABI', 'JAM'],
      dailyAll: data.dailyAll || [],
      daily: data.daily || [],
      schedule: data.schedule || [],
      promo: data.promo || {},
    };
  }, [data]);

  // Date range bounds
  const { minDate, maxDate } = useMemo(() => {
    const dates = raw.daily.map(r => r.date).filter(Boolean).sort();
    return { minDate: dates[0] || '', maxDate: dates[dates.length - 1] || '' };
  }, [raw.daily]);

  // Set defaults once data loads
  useEffect(() => {
    if (minDate && !dateFrom) setDateFrom(minDate);
    if (maxDate && !dateTo) setDateTo(maxDate);
  }, [minDate, maxDate]);

  // Filtered + recomputed data
  const { filteredDaily, filteredDailyAll, filteredTotals, filteredAgentSummaries, filteredSchedule } = useMemo(() => {
    const from = dateFrom || minDate;
    const to = dateTo || maxDate;

    // Filter per-agent daily rows by date + agent
    let fd = raw.daily.filter(r => r.date >= from && r.date <= to);
    if (agentFilter !== 'All') fd = fd.filter(r => r.agent === agentFilter);

    // Recompute dailyAll from filtered rows (handles agent filter correctly)
    const fda = aggregateDailyAll(fd);

    // Recompute totals and agent summaries from filtered rows
    const ft = computeTotals(fd);
    const fas = computeAgentSummaries(fd, agentFilter !== 'All' ? [agentFilter] : raw.agents);

    // Filter schedule by date range
    const fs = raw.schedule.filter(s => s.date >= from && s.date <= to);

    return { filteredDaily: fd, filteredDailyAll: fda, filteredTotals: ft, filteredAgentSummaries: fas, filteredSchedule: fs };
  }, [raw, dateFrom, dateTo, agentFilter, minDate, maxDate]);

  const activeAgents = agentFilter !== 'All' ? [agentFilter] : raw.agents;

  const handleReset = () => {
    setDateFrom(minDate);
    setDateTo(maxDate);
    setAgentFilter('All');
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
    </div>
  );
  if (error) return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-yellow-800">{error}</div>
  );

  const isFiltered = dateFrom !== minDate || dateTo !== maxDate || agentFilter !== 'All';

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Live Streaming Analytics</h1>
        <p className="text-sm text-gray-500 mt-1">TikTok + Bigo performance for SENA, ASHLEY, ABI, JAM</p>
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-xl p-3 shadow-sm border border-gray-100 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-gray-500 uppercase">From</label>
          <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} min={minDate} max={dateTo || maxDate}
            className="px-2 py-1.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-gray-500 uppercase">To</label>
          <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} min={dateFrom || minDate} max={maxDate}
            className="px-2 py-1.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-gray-500 uppercase">Agent</label>
          <select value={agentFilter} onChange={e => setAgentFilter(e.target.value)}
            className="px-2 py-1.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white">
            <option value="All">All Agents</option>
            {raw.agents.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
        {isFiltered && (
          <button onClick={handleReset}
            className="ml-auto px-3 py-1.5 text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors">
            Reset Filters
          </button>
        )}
        <span className="text-xs text-gray-400 ml-auto">{filteredDaily.length} rows · {filteredDailyAll.length} days</span>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 overflow-x-auto pb-1">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
              activeTab === t.id ? 'bg-indigo-600 text-white shadow-sm' : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
            }`}>{t.label}</button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && <OverviewTab totals={filteredTotals} dailyAll={filteredDailyAll} agentSummaries={filteredAgentSummaries} agents={activeAgents} />}
      {activeTab === 'tiktok' && <TikTokTab totals={filteredTotals} dailyAll={filteredDailyAll} agentSummaries={filteredAgentSummaries} agents={activeAgents} />}
      {activeTab === 'bigo' && <BigoTab totals={filteredTotals} dailyAll={filteredDailyAll} agentSummaries={filteredAgentSummaries} agents={activeAgents} />}
      {activeTab === 'compare' && <CompareTab agentSummaries={filteredAgentSummaries} agents={activeAgents} daily={filteredDaily} />}
      {activeTab === 'schedule' && <ScheduleTab schedule={filteredSchedule} />}
      {activeTab === 'daily' && <DailyTab dailyAll={filteredDailyAll} daily={filteredDaily} agents={activeAgents} />}
      {activeTab === 'promo' && <PromoTab promo={raw.promo} agents={raw.agents} />}
    </div>
  );
}

// ══════════════════════════════════════
// TAB: Overview
// ══════════════════════════════════════
function OverviewTab({ totals: t, dailyAll, agentSummaries, agents }) {
  const tkEng = (t.tk_likes || 0) + (t.tk_comments || 0) + (t.tk_shares || 0);
  const bgEng = t.bg_engaged || 0;
  const pieData = [
    { name: 'TikTok', value: tkEng },
    { name: 'Bigo', value: bgEng },
  ].filter(d => d.value > 0);

  // Find top performer
  const topAgent = agents.reduce((best, a) => {
    const eng = agentSummaries[a]?.total_engagement || 0;
    return eng > (agentSummaries[best]?.total_engagement || 0) ? a : best;
  }, agents[0]);

  return (
    <div className="space-y-6">
      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        <StatCard label="TikTok Views" value={fmt(t.tk_views)} color="#00f2ea" />
        <StatCard label="TK Engagement" value={fmt(tkEng)} sub={`${fmt(t.tk_likes)} likes + ${fmt(t.tk_comments)} cmt + ${fmt(t.tk_shares)} share`} color="#00f2ea" />
        <StatCard label="New Followers" value={fmt(t.tk_new_followers)} color="#22c55e" />
        <StatCard label="Bigo Viewers" value={fmt(t.bg_viewers)} color="#a855f7" />
        <StatCard label="Bigo Beans" value={fmt(t.bg_beans)} color="#f59e0b" />
        <StatCard label="Total Engagement" value={fmt(t.total_engagement)} color="#6366f1" />
      </div>

      {/* Top Performer */}
      {topAgent && agentSummaries[topAgent] && (
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl p-5 text-white">
          <p className="text-sm opacity-80">Top Performer</p>
          <p className="text-2xl font-bold mt-1">{topAgent}</p>
          <p className="text-sm opacity-80 mt-1">
            {fmt(agentSummaries[topAgent].total_engagement)} engagement · {fmt(agentSummaries[topAgent].total_reach)} reach
          </p>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Trend */}
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Daily Trend: TikTok Views + Bigo Viewers</h3>
          <ResponsiveContainer width="100%" height={280}>
            <ComposedChart data={dailyAll}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={d => d.slice(5)} />
              <YAxis yAxisId="left" tick={{ fontSize: 10 }} />
              <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar yAxisId="left" dataKey="tk_views" name="TK Views" fill="#00f2ea" opacity={0.7} />
              <Line yAxisId="right" dataKey="bg_viewers" name="BG Viewers" stroke="#a855f7" strokeWidth={2} dot={{ r: 2 }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Platform Pie */}
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Platform Engagement Split</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={3} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                {pieData.map((d, i) => <Cell key={i} fill={PLATFORM_COLORS[d.name]} />)}
              </Pie>
              <Tooltip formatter={(v) => fmt(v)} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Agent Ranking */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Agent Rankings</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-500 uppercase border-b">
                <th className="pb-2 pr-4">#</th><th className="pb-2 pr-4">Agent</th>
                <th className="pb-2 pr-4 text-right">TK Views</th><th className="pb-2 pr-4 text-right">TK Likes</th>
                <th className="pb-2 pr-4 text-right">BG Viewers</th><th className="pb-2 pr-4 text-right">BG Beans</th>
                <th className="pb-2 text-right">Total Eng</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((a, i) => {
                const s = agentSummaries[a] || {};
                return (
                  <tr key={a} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2 pr-4 text-gray-400">#{i + 1}</td>
                    <td className="py-2 pr-4 font-semibold" style={{ color: AGENT_COLORS[a] }}>{a}</td>
                    <td className="py-2 pr-4 text-right">{fmt(s.tk_views)}</td>
                    <td className="py-2 pr-4 text-right">{fmt(s.tk_likes)}</td>
                    <td className="py-2 pr-4 text-right">{fmt(s.bg_viewers)}</td>
                    <td className="py-2 pr-4 text-right">{fmt(s.bg_beans)}</td>
                    <td className="py-2 text-right font-semibold text-indigo-600">{fmt(s.total_engagement)}</td>
                  </tr>
                );
              }).sort((a, b) => (agentSummaries[b.key]?.total_engagement || 0) - (agentSummaries[a.key]?.total_engagement || 0))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════
// TAB: TikTok
// ══════════════════════════════════════
function TikTokTab({ totals: t, dailyAll, agentSummaries, agents }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <StatCard label="Views" value={fmt(t.tk_views)} color="#00f2ea" />
        <StatCard label="Unique Viewers" value={fmt(t.tk_unique)} color="#00d4ff" />
        <StatCard label="Likes" value={fmt(t.tk_likes)} color="#ef4444" />
        <StatCard label="Comments" value={fmt(t.tk_comments)} color="#f59e0b" />
        <StatCard label="Shares" value={fmt(t.tk_shares)} color="#22c55e" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Views + Unique */}
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Views + Unique Viewers</h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={dailyAll}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={d => d.slice(5)} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line dataKey="tk_views" name="Views" stroke="#00f2ea" strokeWidth={2} dot={{ r: 2 }} />
              <Line dataKey="tk_unique" name="Unique" stroke="#00d4ff" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 2 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Engagement stacked area */}
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Likes + Comments + Shares</h3>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={dailyAll}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={d => d.slice(5)} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Area dataKey="tk_likes" name="Likes" stackId="1" stroke="#ef4444" fill="#ef4444" fillOpacity={0.4} />
              <Area dataKey="tk_comments" name="Comments" stackId="1" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.4} />
              <Area dataKey="tk_shares" name="Shares" stackId="1" stroke="#22c55e" fill="#22c55e" fillOpacity={0.4} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Followers */}
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">New Followers</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={dailyAll}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={d => d.slice(5)} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="tk_new_followers" name="New Followers" fill="#22c55e" opacity={0.8} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Agent comparison */}
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Per-Agent TikTok</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={agents.map(a => ({ agent: a, views: agentSummaries[a]?.tk_views || 0, likes: agentSummaries[a]?.tk_likes || 0, comments: agentSummaries[a]?.tk_comments || 0 }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="agent" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="views" name="Views" fill="#00f2ea" />
              <Bar dataKey="likes" name="Likes" fill="#ef4444" />
              <Bar dataKey="comments" name="Comments" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════
// TAB: Bigo
// ══════════════════════════════════════
function BigoTab({ totals: t, dailyAll, agentSummaries, agents }) {
  // Cumulative fans
  const cumData = dailyAll.reduce((acc, d) => {
    const prev = acc.length > 0 ? acc[acc.length - 1].cumFans : 0;
    acc.push({ ...d, cumFans: prev + (d.bg_new_fans || 0) });
    return acc;
  }, []);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Viewers" value={fmt(t.bg_viewers)} color="#a855f7" />
        <StatCard label="Engaged" value={fmt(t.bg_engaged)} color="#c084fc" />
        <StatCard label="Beans" value={fmt(t.bg_beans)} color="#f59e0b" />
        <StatCard label="New Fans" value={fmt(t.bg_new_fans)} color="#22c55e" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Viewers + Engaged</h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={dailyAll}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={d => d.slice(5)} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line dataKey="bg_viewers" name="Viewers" stroke="#a855f7" strokeWidth={2} dot={{ r: 2 }} />
              <Line dataKey="bg_engaged" name="Engaged" stroke="#c084fc" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 2 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Beans Earned</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={dailyAll}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={d => d.slice(5)} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="bg_beans" name="Beans" fill="#f59e0b" opacity={0.8} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Cumulative New Fans</h3>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={cumData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={d => d.slice(5)} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip content={<CustomTooltip />} />
              <Area dataKey="cumFans" name="Cumulative Fans" stroke="#22c55e" fill="#22c55e" fillOpacity={0.15} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Per-Agent Bigo</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={agents.map(a => ({ agent: a, viewers: agentSummaries[a]?.bg_viewers || 0, engaged: agentSummaries[a]?.bg_engaged || 0, beans: agentSummaries[a]?.bg_beans || 0 }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="agent" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="viewers" name="Viewers" fill="#a855f7" />
              <Bar dataKey="engaged" name="Engaged" fill="#c084fc" />
              <Bar dataKey="beans" name="Beans" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════
// TAB: Comparison (Radar + Heatmap)
// ══════════════════════════════════════
function CompareTab({ agentSummaries, agents, daily }) {
  // Normalize for radar
  const metrics = ['tk_views', 'tk_likes', 'bg_viewers', 'bg_beans', 'total_engagement', 'tk_new_followers'];
  const labels = ['TK Views', 'TK Likes', 'BG Viewers', 'BG Beans', 'Engagement', 'Followers'];
  const maxVals = metrics.map(m => Math.max(...agents.map(a => agentSummaries[a]?.[m] || 0), 1));

  const radarData = labels.map((label, i) => {
    const entry = { metric: label };
    agents.forEach(a => {
      entry[a] = Math.round(((agentSummaries[a]?.[metrics[i]] || 0) / maxVals[i]) * 100);
    });
    return entry;
  });

  // Daily heatmap data (agent x date)
  const dates = [...new Set(daily.map(r => r.date))].sort();

  return (
    <div className="space-y-6">
      {/* Radar */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Performance Radar (Normalized 0-100)</h3>
        <ResponsiveContainer width="100%" height={360}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="#e5e7eb" />
            <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11 }} />
            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 9 }} />
            {agents.map(a => (
              <Radar key={a} name={a} dataKey={a} stroke={AGENT_COLORS[a]} fill={AGENT_COLORS[a]} fillOpacity={0.15} strokeWidth={2} />
            ))}
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Tooltip />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Ranking Table */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Performance Ranking</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-500 uppercase border-b">
                <th className="pb-2 pr-3">#</th><th className="pb-2 pr-3">Agent</th>
                <th className="pb-2 pr-3 text-right">TK Views</th><th className="pb-2 pr-3 text-right">TK Likes</th>
                <th className="pb-2 pr-3 text-right">BG Viewers</th><th className="pb-2 pr-3 text-right">BG Beans</th>
                <th className="pb-2 pr-3 text-right">Total Eng</th><th className="pb-2 text-right">Reach</th>
              </tr>
            </thead>
            <tbody>
              {agents
                .map(a => ({ agent: a, ...agentSummaries[a] }))
                .sort((a, b) => (b.total_engagement || 0) - (a.total_engagement || 0))
                .map((r, i) => (
                  <tr key={r.agent} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2 pr-3">{i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `#${i + 1}`}</td>
                    <td className="py-2 pr-3 font-semibold" style={{ color: AGENT_COLORS[r.agent] }}>{r.agent}</td>
                    <td className="py-2 pr-3 text-right">{fmt(r.tk_views)}</td>
                    <td className="py-2 pr-3 text-right">{fmt(r.tk_likes)}</td>
                    <td className="py-2 pr-3 text-right">{fmt(r.bg_viewers)}</td>
                    <td className="py-2 pr-3 text-right">{fmt(r.bg_beans)}</td>
                    <td className="py-2 pr-3 text-right font-semibold text-indigo-600">{fmt(r.total_engagement)}</td>
                    <td className="py-2 text-right">{fmt(r.total_reach)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════
// TAB: Schedule
// ══════════════════════════════════════
function ScheduleTab({ schedule }) {
  if (!schedule.length) return <p className="text-gray-500">No schedule data.</p>;

  const byDate = {};
  schedule.forEach(s => { if (!byDate[s.date]) byDate[s.date] = []; byDate[s.date].push(s); });

  // Platform distribution
  const platCounts = {};
  schedule.forEach(s => { platCounts[s.platform] = (platCounts[s.platform] || 0) + 1; });
  const pieData = Object.entries(platCounts).map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-6">
      {Object.entries(byDate).map(([date, entries]) => (
        <div key={date} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">{date}</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-500 uppercase border-b">
                  <th className="pb-2 pr-3">Time</th><th className="pb-2 pr-3">Streamer</th>
                  <th className="pb-2 pr-3">Platform</th><th className="pb-2 pr-3">Content</th>
                  <th className="pb-2 pr-3">Other Task</th><th className="pb-2">Moderator</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((s, i) => (
                  <tr key={i} className="border-b border-gray-50">
                    <td className="py-2 pr-3 text-gray-600">{s.time}</td>
                    <td className="py-2 pr-3 font-semibold" style={{ color: AGENT_COLORS[s.streamer] || '#374151' }}>{s.streamer}</td>
                    <td className="py-2 pr-3">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium" style={{ backgroundColor: (PLATFORM_COLORS[s.platform] || '#6b7280') + '20', color: PLATFORM_COLORS[s.platform] || '#6b7280' }}>{s.platform}</span>
                    </td>
                    <td className="py-2 pr-3 text-gray-600">{s.content}</td>
                    <td className="py-2 pr-3 text-gray-400 text-xs">{s.other_task}</td>
                    <td className="py-2 text-gray-600">{s.moderator}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}

      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Platform Distribution</h3>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={90} paddingAngle={3} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
              {pieData.map((d, i) => <Cell key={i} fill={PLATFORM_COLORS[d.name] || '#6b7280'} />)}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ══════════════════════════════════════
// TAB: Daily
// ══════════════════════════════════════
function DailyTab({ dailyAll, daily, agents }) {
  // Rolling 7-day avg
  const withAvg = dailyAll.map((d, i) => {
    const start = Math.max(0, i - 6);
    const window = dailyAll.slice(start, i + 1);
    const avg7 = Math.round(window.reduce((s, w) => s + (w.total_engagement || 0), 0) / window.length);
    return { ...d, avg7 };
  });

  return (
    <div className="space-y-6">
      {/* Chart */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Daily Engagement + 7-Day Average</h3>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={withAvg}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={d => d.slice(5)} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Bar dataKey="total_engagement" name="Daily Eng" fill="#6366f1" opacity={0.5} />
            <Line dataKey="avg7" name="7-Day Avg" stroke="#ef4444" strokeWidth={2.5} dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Agent daily stacked */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Per-Agent Daily Engagement</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={(() => {
            const dates = [...new Set(daily.map(r => r.date))].sort();
            return dates.map(date => {
              const entry = { date };
              agents.forEach(a => {
                const row = daily.find(r => r.date === date && r.agent === a);
                entry[a] = row?.total_engagement || 0;
              });
              return entry;
            });
          })()}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={d => d.slice(5)} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            {agents.map(a => <Bar key={a} dataKey={a} stackId="1" fill={AGENT_COLORS[a]} />)}
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Day-by-Day Breakdown</h3>
        <div className="overflow-x-auto max-h-96">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-white">
              <tr className="text-left text-xs text-gray-500 uppercase border-b">
                <th className="pb-2 pr-3">Date</th><th className="pb-2 pr-3 text-right">TK Views</th>
                <th className="pb-2 pr-3 text-right">TK Likes</th><th className="pb-2 pr-3 text-right">BG View</th>
                <th className="pb-2 pr-3 text-right">BG Beans</th><th className="pb-2 text-right">Total Eng</th>
              </tr>
            </thead>
            <tbody>
              {[...dailyAll].reverse().map(d => (
                <tr key={d.date} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-1.5 pr-3">{d.date}</td>
                  <td className="py-1.5 pr-3 text-right">{fmt(d.tk_views)}</td>
                  <td className="py-1.5 pr-3 text-right">{fmt(d.tk_likes)}</td>
                  <td className="py-1.5 pr-3 text-right">{fmt(d.bg_viewers)}</td>
                  <td className="py-1.5 pr-3 text-right">{fmt(d.bg_beans)}</td>
                  <td className="py-1.5 text-right font-semibold text-indigo-600">{fmt(d.total_engagement)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════
// TAB: Promo Codes
// ══════════════════════════════════════
function PromoTab({ promo, agents }) {
  const [search, setSearch] = useState('');

  return (
    <div className="space-y-6">
      {/* Agent stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {agents.map(a => {
          const p = promo[a] || { used: 0, unused: 0, expired: 0, total: 0, usage_rate: 0 };
          return (
            <div key={a} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <p className="text-xs text-gray-500 uppercase">{a}</p>
              <p className="text-2xl font-bold mt-1" style={{ color: AGENT_COLORS[a] }}>{p.total}</p>
              <div className="flex gap-2 mt-2 text-xs">
                <span className="px-1.5 py-0.5 rounded bg-green-100 text-green-700">{p.used} Used</span>
                <span className="px-1.5 py-0.5 rounded bg-yellow-100 text-yellow-700">{p.unused} Unused</span>
                <span className="px-1.5 py-0.5 rounded bg-red-100 text-red-700">{p.expired} Exp</span>
              </div>
              <p className="text-xs mt-1" style={{ color: p.usage_rate > 70 ? '#16a34a' : p.usage_rate > 40 ? '#ca8a04' : '#dc2626' }}>{pct(p.usage_rate)} usage</p>
            </div>
          );
        })}
      </div>

      {/* Stacked bar */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Code Status by Agent</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={agents.map(a => ({ agent: a, used: promo[a]?.used || 0, unused: promo[a]?.unused || 0, expired: promo[a]?.expired || 0 }))}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="agent" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Bar dataKey="used" stackId="1" name="Used" fill="#22c55e" />
            <Bar dataKey="unused" stackId="1" name="Unused" fill="#f59e0b" />
            <Bar dataKey="expired" stackId="1" name="Expired" fill="#ef4444" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Searchable table */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <div className="flex items-center gap-3 mb-3">
          <h3 className="text-sm font-semibold text-gray-700">All Promo Codes</h3>
          <input type="text" placeholder="Search codes..." value={search} onChange={e => setSearch(e.target.value)}
            className="ml-auto px-3 py-1.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
        <div className="overflow-y-auto max-h-96">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-white">
              <tr className="text-left text-xs text-gray-500 uppercase border-b">
                <th className="pb-2 pr-3">Agent</th><th className="pb-2 pr-3">Code</th><th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {agents.flatMap(a => (promo[a]?.codes || []).map(c => ({ agent: a, ...c })))
                .filter(c => !search || c.code.toLowerCase().includes(search.toLowerCase()))
                .map((c, i) => (
                  <tr key={i} className="border-b border-gray-50">
                    <td className="py-1.5 pr-3 font-medium" style={{ color: AGENT_COLORS[c.agent] }}>{c.agent}</td>
                    <td className="py-1.5 pr-3">{c.code}</td>
                    <td className="py-1.5">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        c.status === 'USED' ? 'bg-green-100 text-green-700' :
                        c.status === 'EXPIRED' ? 'bg-red-100 text-red-700' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>{c.status || 'UNUSED'}</span>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
