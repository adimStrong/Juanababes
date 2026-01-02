#!/usr/bin/env python3
"""
JuanBabes Deep Dive Analytics Report Generator
Analyzes why Abi, Jam, and Zell have fewer followers than Ashley and Sena
Data collected via Playwright on Dec 31, 2025
"""

import os
from datetime import datetime

# Live Facebook Data (collected Dec 31, 2025)
JUANBABES_DATA = {
    "Ashley": {
        "followers": 44000,
        "reels_count": 48,
        "avg_views": 15000,
        "top_viral": 172000,
        "viral_hits": [172000, 157000, 128000, 105000, 92000, 75000],
        "typical_views": "5K-30K",
        "status": "TOP",
        "color": "#10B981",  # Green
        "page_url": "https://www.facebook.com/JuanababeAshley"
    },
    "Sena": {
        "followers": 16000,
        "reels_count": 122,
        "avg_views": 1000,
        "top_viral": 103000,
        "viral_hits": [103000, 79000, 16000, 9300],
        "typical_views": "500-2K",
        "status": "GROWING",
        "color": "#3B82F6",  # Blue
        "page_url": "https://www.facebook.com/JuanababeSena"
    },
    "Zell": {
        "followers": 2200,
        "reels_count": 47,
        "avg_views": 600,
        "top_viral": 2400,
        "viral_hits": [],
        "typical_views": "200-900",
        "status": "LOW",
        "color": "#F59E0B",  # Amber
        "page_url": "https://www.facebook.com/JuanababeZell"
    },
    "Jam": {
        "followers": 1900,
        "reels_count": 59,
        "avg_views": 500,
        "top_viral": 5400,
        "viral_hits": [],
        "typical_views": "100-900",
        "status": "LOW",
        "color": "#8B5CF6",  # Purple
        "page_url": "https://www.facebook.com/JuanababeJam"
    },
    "Abi": {
        "followers": 1100,
        "reels_count": 82,
        "avg_views": 400,
        "top_viral": 3600,
        "viral_hits": [],
        "typical_views": "200-600",
        "status": "LOWEST",
        "color": "#EF4444",  # Red
        "page_url": "https://www.facebook.com/JuanababeAbi"
    }
}

def generate_html_report():
    """Generate the Deep Dive HTML Report"""

    # Calculate key metrics
    ashley = JUANBABES_DATA["Ashley"]
    abi = JUANBABES_DATA["Abi"]

    followers_gap = ashley["followers"] / abi["followers"]
    views_gap = ashley["avg_views"] / abi["avg_views"]
    abi_effort = abi["reels_count"] / (abi["followers"] / 1000)
    ashley_effort = ashley["reels_count"] / (ashley["followers"] / 1000)
    effort_ratio = abi_effort / ashley_effort

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JuanBabes Deep Dive Analytics Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4c1d95 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            padding: 40px 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }}

        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #f472b6, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .header .subtitle {{
            font-size: 1.2rem;
            opacity: 0.8;
        }}

        .header .date {{
            font-size: 0.9rem;
            opacity: 0.6;
            margin-top: 10px;
        }}

        .core-question {{
            background: linear-gradient(135deg, #ec4899, #8b5cf6);
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 30px;
            font-size: 1.3rem;
            font-weight: 600;
        }}

        .insight-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .insight-card {{
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}

        .insight-card.highlight {{
            background: linear-gradient(135deg, rgba(239,68,68,0.3), rgba(236,72,153,0.3));
            border: 2px solid #f472b6;
        }}

        .insight-card h3 {{
            font-size: 0.9rem;
            text-transform: uppercase;
            opacity: 0.7;
            margin-bottom: 10px;
        }}

        .insight-card .value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: #f472b6;
        }}

        .insight-card .description {{
            font-size: 0.95rem;
            opacity: 0.8;
            margin-top: 10px;
        }}

        .section {{
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }}

        .section h2 {{
            font-size: 1.5rem;
            margin-bottom: 20px;
            color: #a5b4fc;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}

        .data-table th, .data-table td {{
            padding: 15px;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}

        .data-table th {{
            background: rgba(255,255,255,0.1);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85rem;
            letter-spacing: 1px;
        }}

        .data-table tr:hover {{
            background: rgba(255,255,255,0.05);
        }}

        .status-badge {{
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .status-top {{ background: #10B981; color: white; }}
        .status-growing {{ background: #3B82F6; color: white; }}
        .status-low {{ background: #F59E0B; color: black; }}
        .status-lowest {{ background: #EF4444; color: white; }}

        .chart-container {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
            margin-top: 20px;
        }}

        .chart-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }}

        .feedback-loop {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }}

        .loop-box {{
            padding: 25px;
            border-radius: 15px;
            text-align: center;
        }}

        .loop-box.winner {{
            background: linear-gradient(135deg, rgba(16,185,129,0.3), rgba(59,130,246,0.3));
            border: 2px solid #10B981;
        }}

        .loop-box.loser {{
            background: linear-gradient(135deg, rgba(239,68,68,0.3), rgba(245,158,11,0.3));
            border: 2px solid #EF4444;
        }}

        .loop-box h3 {{
            font-size: 1.2rem;
            margin-bottom: 15px;
        }}

        .loop-box .flow {{
            font-family: monospace;
            font-size: 0.9rem;
            line-height: 1.8;
            text-align: left;
            padding: 15px;
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
        }}

        .recommendations {{
            margin-top: 20px;
        }}

        .rec-category {{
            margin-bottom: 25px;
        }}

        .rec-category h3 {{
            color: #f472b6;
            margin-bottom: 15px;
            font-size: 1.1rem;
        }}

        .rec-list {{
            list-style: none;
        }}

        .rec-list li {{
            padding: 12px 15px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            margin-bottom: 10px;
            border-left: 4px solid #818cf8;
        }}

        .rec-list li strong {{
            color: #a5b4fc;
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            opacity: 0.6;
            font-size: 0.85rem;
        }}

        @media (max-width: 768px) {{
            .header h1 {{ font-size: 1.8rem; }}
            .insight-cards {{ grid-template-columns: 1fr; }}
            .feedback-loop {{ grid-template-columns: 1fr; }}
            .chart-row {{ grid-template-columns: 1fr; }}
        }}

        @media print {{
            body {{ background: white; color: black; }}
            .section {{ background: #f5f5f5; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>JuanBabes Deep Dive Analytics</h1>
            <div class="subtitle">Understanding the Follower Gap Between 5 Juana Babe Pages</div>
            <div class="date">Data collected: December 31, 2025 via Facebook</div>
        </div>

        <div class="core-question">
            Why do Abi, Jam, and Zell have fewer followers than Ashley and Sena?
        </div>

        <div class="insight-cards">
            <div class="insight-card highlight">
                <h3>The Follower Gap</h3>
                <div class="value">{followers_gap:.0f}x</div>
                <div class="description">Ashley has {followers_gap:.0f}x more followers than Abi despite having fewer reels</div>
            </div>
            <div class="insight-card">
                <h3>Views Per Reel Gap</h3>
                <div class="value">{views_gap:.0f}x</div>
                <div class="description">Ashley's reels get {views_gap:.0f}x more views on average than Abi's</div>
            </div>
            <div class="insight-card highlight">
                <h3>Effort Ratio</h3>
                <div class="value">{effort_ratio:.0f}x</div>
                <div class="description">Abi works {effort_ratio:.0f}x harder per follower than Ashley!</div>
            </div>
            <div class="insight-card">
                <h3>The Viral Threshold</h3>
                <div class="value">10K+</div>
                <div class="description">Only Ashley & Sena have reels with 10K+ views - the viral threshold</div>
            </div>
        </div>

        <div class="section">
            <h2>📊 Complete Data (All 5 Pages)</h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Page</th>
                        <th>Followers</th>
                        <th>Reels</th>
                        <th>Avg Views</th>
                        <th>Top Viral</th>
                        <th>Viral Hits (10K+)</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
'''

    # Add data rows
    for name, data in JUANBABES_DATA.items():
        status_class = data["status"].lower().replace(" ", "-")
        viral_count = len(data["viral_hits"]) if data["viral_hits"] else 0
        html += f'''
                    <tr>
                        <td><strong style="color: {data['color']}">{name}</strong></td>
                        <td>{data['followers']:,}</td>
                        <td>{data['reels_count']}</td>
                        <td>~{data['avg_views']:,}</td>
                        <td>{data['top_viral']:,}</td>
                        <td>{viral_count if viral_count > 0 else "0"}</td>
                        <td><span class="status-badge status-{status_class}">{data['status']}</span></td>
                    </tr>
'''

    html += '''
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>📈 Visual Analysis</h2>
            <div class="chart-row">
                <div class="chart-container">
                    <canvas id="followersChart"></canvas>
                </div>
                <div class="chart-container">
                    <canvas id="reelsVsFollowersChart"></canvas>
                </div>
            </div>
            <div class="chart-row" style="margin-top: 20px;">
                <div class="chart-container">
                    <canvas id="avgViewsChart"></canvas>
                </div>
                <div class="chart-container">
                    <canvas id="effortChart"></canvas>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>🔄 The Algorithm Feedback Loop</h2>
            <div class="feedback-loop">
                <div class="loop-box winner">
                    <h3>✅ Winners Path (Ashley & Sena)</h3>
                    <div class="flow">
Early viral hit (100K+)<br>
    ↓<br>
Algorithm boost → More reach<br>
    ↓<br>
More followers join<br>
    ↓<br>
Higher initial views on new content<br>
    ↓<br>
More viral hits → Snowball growth 📈
                    </div>
                </div>
                <div class="loop-box loser">
                    <h3>❌ Struggling Path (Abi, Jam, Zell)</h3>
                    <div class="flow">
No early viral hit<br>
    ↓<br>
Algorithm doesn't push content<br>
    ↓<br>
Low reach (200-600 views)<br>
    ↓<br>
Can't go viral with low views<br>
    ↓<br>
Stuck at 1-2K followers 📉
                    </div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>💡 Key Insights</h2>
            <div class="insight-cards">
                <div class="insight-card">
                    <h3>Content Volume ≠ Success</h3>
                    <div class="description">
                        <strong>Abi has 82 reels → 1.1K followers</strong><br>
                        <strong>Ashley has 48 reels → 44K followers</strong><br><br>
                        More content doesn't mean more followers. Quality and virality matter more.
                    </div>
                </div>
                <div class="insight-card">
                    <h3>Viral Content is the Key</h3>
                    <div class="description">
                        <strong>Ashley:</strong> 6+ reels with 100K+ views<br>
                        <strong>Sena:</strong> 4 reels with 10K+ views<br>
                        <strong>Abi/Jam/Zell:</strong> 0 viral hits<br><br>
                        One viral reel can change everything.
                    </div>
                </div>
                <div class="insight-card">
                    <h3>Sena Shows the Middle Path</h3>
                    <div class="description">
                        Sena has the MOST reels (122) and SOME viral hits (103K, 79K).<br><br>
                        Result: 16K followers - not as high as Ashley, but growing.
                    </div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>🎯 Recommendations for Abi, Jam & Zell</h2>
            <div class="recommendations">
                <div class="rec-category">
                    <h3>🚀 Immediate Actions</h3>
                    <ul class="rec-list">
                        <li><strong>Paid Boost:</strong> Spend ₱500-1000 to boost your best-performing reel. This can kickstart the algorithm.</li>
                        <li><strong>Collab with Ashley:</strong> Appear in Ashley's viral reels for instant exposure to her 44K followers.</li>
                        <li><strong>Cross-Promotion:</strong> Get the main Juan365 page to share your best content.</li>
                        <li><strong>Trending Sounds:</strong> Use the same sounds/music as Ashley's viral reels.</li>
                    </ul>
                </div>
                <div class="rec-category">
                    <h3>📝 Content Strategy</h3>
                    <ul class="rec-list">
                        <li><strong>Study Ashley's Viral Reels:</strong> What hooks viewers in the first 3 seconds?</li>
                        <li><strong>Replicate Success:</strong> Create similar content with the same energy and style.</li>
                        <li><strong>Post at Peak Times:</strong> When does Ashley post? Post at the same times.</li>
                        <li><strong>Use Viral Hashtags:</strong> Copy hashtags from Ashley's top-performing reels.</li>
                    </ul>
                </div>
                <div class="rec-category">
                    <h3>📊 Long-term Mindset</h3>
                    <ul class="rec-list">
                        <li><strong>Quality > Quantity:</strong> Ashley has 48 reels but 44K followers. Abi has 82 reels but 1.1K followers.</li>
                        <li><strong>Focus on Shareability:</strong> Create content people want to share, not just watch.</li>
                        <li><strong>One Viral Hit Changes Everything:</strong> Keep trying - Sena's 103K reel helped grow to 16K followers.</li>
                    </ul>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
            <p>JuanBabes Deep Dive Analytics Report</p>
        </div>
    </div>

    <script>
        // Chart.js Configuration
        Chart.defaults.color = '#a5b4fc';
        Chart.defaults.borderColor = 'rgba(255,255,255,0.1)';

        // Followers Chart
        new Chart(document.getElementById('followersChart'), {{
            type: 'bar',
            data: {{
                labels: ['Ashley', 'Sena', 'Zell', 'Jam', 'Abi'],
                datasets: [{{
                    label: 'Followers',
                    data: [44000, 16000, 2200, 1900, 1100],
                    backgroundColor: ['#10B981', '#3B82F6', '#F59E0B', '#8B5CF6', '#EF4444'],
                    borderRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Followers Comparison',
                        font: {{ size: 16 }}
                    }},
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{ color: 'rgba(255,255,255,0.1)' }}
                    }},
                    x: {{
                        grid: {{ display: false }}
                    }}
                }}
            }}
        }});

        // Reels vs Followers Chart
        new Chart(document.getElementById('reelsVsFollowersChart'), {{
            type: 'scatter',
            data: {{
                datasets: [{{
                    label: 'Pages',
                    data: [
                        {{ x: 48, y: 44000, label: 'Ashley' }},
                        {{ x: 122, y: 16000, label: 'Sena' }},
                        {{ x: 47, y: 2200, label: 'Zell' }},
                        {{ x: 59, y: 1900, label: 'Jam' }},
                        {{ x: 82, y: 1100, label: 'Abi' }}
                    ],
                    backgroundColor: ['#10B981', '#3B82F6', '#F59E0B', '#8B5CF6', '#EF4444'],
                    pointRadius: 15
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Reels Count vs Followers (More Reels ≠ More Followers!)',
                        font: {{ size: 16 }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const labels = ['Ashley', 'Sena', 'Zell', 'Jam', 'Abi'];
                                return labels[context.dataIndex] + ': ' + context.raw.x + ' reels, ' + context.raw.y.toLocaleString() + ' followers';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        title: {{ display: true, text: 'Number of Reels' }},
                        grid: {{ color: 'rgba(255,255,255,0.1)' }}
                    }},
                    y: {{
                        title: {{ display: true, text: 'Followers' }},
                        grid: {{ color: 'rgba(255,255,255,0.1)' }}
                    }}
                }}
            }}
        }});

        // Average Views Chart
        new Chart(document.getElementById('avgViewsChart'), {{
            type: 'bar',
            data: {{
                labels: ['Ashley', 'Sena', 'Zell', 'Jam', 'Abi'],
                datasets: [{{
                    label: 'Avg Views per Reel',
                    data: [15000, 1000, 600, 500, 400],
                    backgroundColor: ['#10B981', '#3B82F6', '#F59E0B', '#8B5CF6', '#EF4444'],
                    borderRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Average Views per Reel',
                        font: {{ size: 16 }}
                    }},
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{ color: 'rgba(255,255,255,0.1)' }}
                    }},
                    x: {{
                        grid: {{ display: false }}
                    }}
                }}
            }}
        }});

        // Effort Chart (Reels per 1K Followers)
        new Chart(document.getElementById('effortChart'), {{
            type: 'bar',
            data: {{
                labels: ['Ashley', 'Sena', 'Zell', 'Jam', 'Abi'],
                datasets: [{{
                    label: 'Reels per 1K Followers',
                    data: [1.1, 7.6, 21.4, 31.1, 74.5],
                    backgroundColor: ['#10B981', '#3B82F6', '#F59E0B', '#8B5CF6', '#EF4444'],
                    borderRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Effort Ratio: Reels per 1K Followers (Lower = More Efficient)',
                        font: {{ size: 16 }}
                    }},
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{ color: 'rgba(255,255,255,0.1)' }}
                    }},
                    x: {{
                        grid: {{ display: false }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
'''

    # Fix JavaScript curly braces (f-string escaping issue)
    # Replace double braces with single braces in JavaScript sections
    html = html.replace('{{', '{').replace('}}', '}')

    return html


def main():
    """Main function to generate the report"""
    print("=" * 60)
    print("JuanBabes Deep Dive Analytics Report Generator")
    print("=" * 60)

    # Ensure reports directory exists
    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(reports_dir, exist_ok=True)

    # Generate HTML
    print("\nGenerating HTML report...")
    html_content = generate_html_report()

    # Save to file
    output_path = os.path.join(reports_dir, "juanbabes_deep_dive.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\n[OK] Report generated: {output_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("KEY FINDINGS:")
    print("=" * 60)
    print("\nData Summary:")
    print("-" * 50)
    for name, data in JUANBABES_DATA.items():
        viral_count = len(data["viral_hits"]) if data["viral_hits"] else 0
        print(f"  {name:8} | {data['followers']:>6,} followers | {data['reels_count']:>3} reels | Viral: {viral_count}")

    print("\nKey Insight:")
    print("   Abi works 74x HARDER per follower than Ashley!")
    print("   (Abi: 82 reels - 1.1K followers)")
    print("   (Ashley: 48 reels - 44K followers)")

    print("\nThe Problem:")
    print("   Abi, Jam, Zell have ZERO viral hits (10K+ views)")
    print("   Ashley has 6+ reels with 100K+ views")
    print("   Without viral content, growth is capped")

    return output_path


if __name__ == "__main__":
    output_file = main()
