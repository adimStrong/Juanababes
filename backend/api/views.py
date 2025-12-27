"""
Django REST Framework views for JuanBabes Analytics API
Updated for 5 pages with direct post metrics
"""

import csv
import io
from datetime import datetime, timedelta
from django.db.models import Sum, Avg, Count, Min, Max, F
from django.db.models.functions import TruncDate
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters import rest_framework as filters

from .models import Page, Post, PostMetrics, CsvImport, AudienceOverlap
from .serializers import (
    PageSerializer, PostListSerializer, PostDetailSerializer,
    PostMetricsSerializer, CsvImportSerializer, AudienceOverlapSerializer,
    DashboardStatsSerializer, DailyEngagementSerializer, PostTypeStatsSerializer
)


class PageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Facebook pages."""
    queryset = Page.objects.all()
    serializer_class = PageSerializer
    filterset_fields = ['is_competitor']
    search_fields = ['page_name']
    ordering_fields = ['page_name', 'fan_count', 'followers_count']


class PostFilter(filters.FilterSet):
    """Filter for posts."""
    start_date = filters.DateFilter(field_name='publish_time', lookup_expr='gte')
    end_date = filters.DateFilter(field_name='publish_time', lookup_expr='lte')
    page = filters.CharFilter(field_name='page_id')

    class Meta:
        model = Post
        fields = ['page', 'post_type', 'is_crosspost', 'is_share']


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for posts."""
    queryset = Post.objects.select_related('page').prefetch_related('metrics')
    filterset_class = PostFilter
    search_fields = ['title', 'description']
    ordering_fields = ['publish_time', 'post_type']
    ordering = ['-publish_time']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PostDetailSerializer
        return PostListSerializer


class CsvImportViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for CSV import history."""
    queryset = CsvImport.objects.all()
    serializer_class = CsvImportSerializer
    filterset_fields = ['status']
    ordering = ['-import_date']


class AudienceOverlapViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for audience overlap analysis."""
    queryset = AudienceOverlap.objects.select_related('page_1', 'page_2')
    serializer_class = AudienceOverlapSerializer
    ordering = ['-analysis_date']


class DashboardStatsView(APIView):
    """Dashboard summary statistics - now using direct post columns."""

    def get(self, request):
        from django.db import connection

        with connection.cursor() as cursor:
            # Get totals directly from posts table
            cursor.execute("""
                SELECT
                    COALESCE(SUM(reactions_total), 0) as total_reactions,
                    COALESCE(SUM(comments_count), 0) as total_comments,
                    COALESCE(SUM(shares_count), 0) as total_shares,
                    COALESCE(SUM(total_engagement), 0) as total_engagement,
                    COALESCE(SUM(pes), 0) as total_pes
                FROM posts
                WHERE reactions_total > 0 OR comments_count > 0 OR shares_count > 0
            """)
            row = cursor.fetchone()
            total_reactions = row[0] or 0
            total_comments = row[1] or 0
            total_shares = row[2] or 0
            total_engagement = row[3] or 0
            total_pes = row[4] or 0

            # Get date range
            cursor.execute("""
                SELECT MIN(publish_time), MAX(publish_time)
                FROM posts
                WHERE publish_time IS NOT NULL
            """)
            date_row = cursor.fetchone()
            start_date = str(date_row[0])[:10] if date_row[0] else None
            end_date = str(date_row[1])[:10] if date_row[1] else None

            # Get counts
            cursor.execute("SELECT COUNT(*) FROM posts WHERE reactions_total > 0 OR comments_count > 0")
            post_count = cursor.fetchone()[0]

            # Count unique pages with posts
            cursor.execute("""
                SELECT COUNT(DISTINCT page_id) FROM posts
                WHERE reactions_total > 0 OR comments_count > 0
            """)
            active_page_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM pages")
            total_page_count = cursor.fetchone()[0]

        avg_engagement = total_engagement / post_count if post_count > 0 else 0
        avg_pes = total_pes / post_count if post_count > 0 else 0

        stats = {
            'total_posts': post_count,
            'total_pages': active_page_count,
            'all_pages': total_page_count,
            'total_reactions': total_reactions,
            'total_comments': total_comments,
            'total_shares': total_shares,
            'total_engagement': total_engagement,
            'total_pes': round(total_pes, 1),
            'avg_engagement': round(avg_engagement, 1),
            'avg_pes': round(avg_pes, 1),
            'date_range_start': start_date,
            'date_range_end': end_date,
        }

        return Response(stats)


class DailyEngagementView(APIView):
    """Daily engagement statistics for charts."""

    def get(self, request):
        from django.db import connection

        days = int(request.query_params.get('days', 30))
        page_id = request.query_params.get('page')

        page_filter = f"AND page_id = '{page_id}'" if page_id else ""

        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT
                    DATE(publish_time) as post_date,
                    COUNT(*) as post_count,
                    COALESCE(SUM(reactions_total), 0) as reactions,
                    COALESCE(SUM(comments_count), 0) as comments,
                    COALESCE(SUM(shares_count), 0) as shares,
                    COALESCE(SUM(total_engagement), 0) as engagement,
                    COALESCE(SUM(pes), 0) as pes
                FROM posts
                WHERE publish_time IS NOT NULL
                    AND DATE(publish_time) >= DATE('now', '-{days} days')
                    AND (reactions_total > 0 OR comments_count > 0 OR shares_count > 0)
                    {page_filter}
                GROUP BY DATE(publish_time)
                ORDER BY post_date
            """)

            result = []
            for row in cursor.fetchall():
                result.append({
                    'date': row[0],
                    'posts': row[1],
                    'reactions': row[2],
                    'comments': row[3],
                    'shares': row[4],
                    'engagement': row[5],
                    'pes': round(row[6], 1)
                })

        return Response(result)


class PostTypeStatsView(APIView):
    """Post type distribution statistics."""

    def get(self, request):
        from django.db import connection

        page_id = request.query_params.get('page')
        page_filter = f"AND page_id = '{page_id}'" if page_id else ""

        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT
                    COALESCE(post_type, 'Unknown') as post_type,
                    COUNT(*) as count,
                    COALESCE(SUM(reactions_total), 0) as reactions,
                    COALESCE(SUM(comments_count), 0) as comments,
                    COALESCE(SUM(shares_count), 0) as shares,
                    COALESCE(SUM(total_engagement), 0) as total_engagement,
                    COALESCE(AVG(pes), 0) as avg_pes
                FROM posts
                WHERE (reactions_total > 0 OR comments_count > 0 OR shares_count > 0)
                    {page_filter}
                GROUP BY post_type
                ORDER BY count DESC
            """)

            result = []
            for row in cursor.fetchall():
                count = row[1]
                total_engagement = row[5]
                result.append({
                    'post_type': row[0],
                    'count': count,
                    'reactions': row[2],
                    'comments': row[3],
                    'shares': row[4],
                    'total_engagement': total_engagement,
                    'avg_engagement': round(total_engagement / count, 1) if count > 0 else 0,
                    'avg_pes': round(row[6], 1)
                })

        return Response(result)


class TopPostsView(APIView):
    """Top performing posts."""

    def get(self, request):
        from django.db import connection

        limit = int(request.query_params.get('limit', 10))
        metric = request.query_params.get('metric', 'engagement')
        page_id = request.query_params.get('page')

        page_filter = f"AND p.page_id = '{page_id}'" if page_id else ""

        # Map metric to SQL column
        order_by = {
            'engagement': 'total_engagement',
            'reactions': 'reactions_total',
            'comments': 'comments_count',
            'shares': 'shares_count',
            'pes': 'pes',
        }.get(metric, 'total_engagement')

        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT
                    p.post_id,
                    pg.page_name,
                    p.title,
                    p.post_type,
                    p.publish_time,
                    p.permalink,
                    COALESCE(p.reactions_total, 0) as reactions,
                    COALESCE(p.comments_count, 0) as comments,
                    COALESCE(p.shares_count, 0) as shares,
                    COALESCE(p.total_engagement, 0) as engagement,
                    COALESCE(p.pes, 0) as pes
                FROM posts p
                LEFT JOIN pages pg ON p.page_id = pg.page_id
                WHERE (p.reactions_total > 0 OR p.comments_count > 0 OR p.shares_count > 0)
                    {page_filter}
                ORDER BY p.{order_by} DESC
                LIMIT {limit}
            """)

            result = []
            for row in cursor.fetchall():
                result.append({
                    'post_id': row[0],
                    'page_name': row[1],
                    'title': row[2],
                    'post_type': row[3],
                    'publish_time': row[4],
                    'permalink': row[5],
                    'reactions': row[6],
                    'comments': row[7],
                    'shares': row[8],
                    'engagement': row[9],
                    'pes': round(row[10], 1),
                })

        return Response(result)


class PageComparisonView(APIView):
    """Compare engagement across pages."""

    def get(self, request):
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    pg.page_id,
                    pg.page_name,
                    pg.fan_count,
                    pg.followers_count,
                    COUNT(p.post_id) as post_count,
                    COALESCE(SUM(p.reactions_total), 0) as total_reactions,
                    COALESCE(SUM(p.comments_count), 0) as total_comments,
                    COALESCE(SUM(p.shares_count), 0) as total_shares,
                    COALESCE(SUM(p.total_engagement), 0) as total_engagement,
                    COALESCE(AVG(p.pes), 0) as avg_pes
                FROM pages pg
                LEFT JOIN posts p ON pg.page_id = p.page_id
                    AND (p.reactions_total > 0 OR p.comments_count > 0 OR p.shares_count > 0)
                GROUP BY pg.page_id, pg.page_name, pg.fan_count, pg.followers_count
                HAVING COUNT(p.post_id) > 0
                ORDER BY total_engagement DESC
            """)

            result = []
            for row in cursor.fetchall():
                post_count = row[4]
                total_engagement = row[8]
                result.append({
                    'page_id': row[0],
                    'page_name': row[1],
                    'fan_count': row[2],
                    'followers_count': row[3],
                    'post_count': post_count,
                    'total_reactions': row[5],
                    'total_comments': row[6],
                    'total_shares': row[7],
                    'total_engagement': total_engagement,
                    'avg_engagement': round(total_engagement / post_count, 1) if post_count > 0 else 0,
                    'avg_pes': round(row[9], 1)
                })

        return Response(result)


class CsvImportView(APIView):
    """Import CSV data from Meta Business Suite export."""
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        from django.db import connection

        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file uploaded'}, status=400)

        if not file.name.endswith('.csv'):
            return Response({'error': 'File must be a CSV'}, status=400)

        try:
            # Read CSV content
            content = file.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(content))

            imported = 0
            pages_seen = set()

            with connection.cursor() as cursor:
                for row in reader:
                    page_id = row.get('Page ID', '')
                    page_name = row.get('Page name', '')
                    post_id = row.get('Post ID', '')

                    if not post_id or not page_id:
                        continue

                    # Track pages
                    if page_id not in pages_seen:
                        pages_seen.add(page_id)
                        cursor.execute("""
                            INSERT OR IGNORE INTO pages (page_id, page_name, created_at, updated_at)
                            VALUES (?, ?, ?, ?)
                        """, (page_id, page_name, datetime.now().isoformat(), datetime.now().isoformat()))

                    # Parse post data
                    title = (row.get('Title', '') or '')[:200]
                    permalink = row.get('Permalink', '') or ''
                    post_type = row.get('Post type', 'TEXT') or 'TEXT'

                    # Parse datetime
                    publish_time_str = row.get('Publish time', '')
                    try:
                        publish_time = datetime.strptime(publish_time_str, "%m/%d/%Y %H:%M").isoformat() if publish_time_str else None
                    except:
                        publish_time = publish_time_str

                    # Parse metrics
                    def safe_int(val):
                        try:
                            return int(float(val)) if val else 0
                        except:
                            return 0

                    reactions = safe_int(row.get('Reactions', 0))
                    comments = safe_int(row.get('Comments', 0))
                    shares = safe_int(row.get('Shares', 0))

                    total_engagement = reactions + comments + shares
                    pes = (reactions * 1.0) + (comments * 2.0) + (shares * 3.0)

                    # Insert or update post
                    cursor.execute("""
                        INSERT OR REPLACE INTO posts
                        (post_id, page_id, title, permalink, post_type, publish_time,
                         reactions_total, comments_count, shares_count,
                         pes, total_engagement, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        post_id, page_id, title, permalink, post_type, publish_time,
                        reactions, comments, shares, pes, total_engagement,
                        datetime.now().isoformat()
                    ))
                    imported += 1

            # Log import
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO csv_imports (filename, import_date, rows_imported, rows_updated, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (file.name, datetime.now().isoformat(), imported, 0, 'completed'))

            return Response({
                'success': True,
                'posts_imported': imported,
                'pages_count': len(pages_seen),
                'pages': list(pages_seen)
            })

        except Exception as e:
            return Response({'error': str(e)}, status=500)
