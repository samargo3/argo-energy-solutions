#!/usr/bin/env python3
"""
Natural Language Energy Data Query Tool

Quick and easy way to query your Neon database with simple questions.

Usage:
    python query_energy_data.py "show me total energy this week"
    python query_energy_data.py "what's the average power for RTU-1"
    python query_energy_data.py "list all channels"
"""

import os
import sys
import psycopg2
from pathlib import Path
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))
load_dotenv(_PROJECT_ROOT / '.env')


class EnergyDataQuery:
    """Simple natural language query interface for energy data"""
    
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL not found in environment")
    
    def _get_connection(self):
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
    
    def _format_table(self, rows, headers=None):
        """Format query results as a nice table"""
        if not rows:
            return "No results found."
        
        if headers is None:
            headers = list(rows[0].keys())
        
        # Calculate column widths
        widths = {h: len(str(h)) for h in headers}
        for row in rows:
            for h in headers:
                widths[h] = max(widths[h], len(str(row.get(h, ''))))
        
        # Build table
        lines = []
        
        # Header
        header_line = " | ".join(str(h).ljust(widths[h]) for h in headers)
        lines.append(header_line)
        lines.append("-" * len(header_line))
        
        # Rows
        for row in rows:
            lines.append(" | ".join(str(row.get(h, '')).ljust(widths[h]) for h in headers))
        
        return "\n".join(lines)
    
    def list_channels(self):
        """List all channels"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        channel_id,
                        channel_name,
                        channel_type,
                        organization_id
                    FROM channels
                    ORDER BY channel_name
                """)
                return self._format_table(cur.fetchall())
    
    def get_channel_stats(self, channel_name=None, days=7):
        """Get statistics for a channel"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                if channel_name:
                    cur.execute("""
                        SELECT 
                            c.channel_name,
                            COUNT(r.id) as reading_count,
                            ROUND(AVG(r.power_kw)::numeric, 2) as avg_power_kw,
                            ROUND(MAX(r.power_kw)::numeric, 2) as max_power_kw,
                            ROUND(MIN(r.power_kw)::numeric, 2) as min_power_kw,
                            ROUND(SUM(r.energy_kwh)::numeric, 2) as total_energy_kwh,
                            MIN(r.timestamp) as first_reading,
                            MAX(r.timestamp) as last_reading
                        FROM channels c
                        LEFT JOIN readings r ON c.channel_id = r.channel_id
                        WHERE c.channel_name ILIKE %s
                            AND r.timestamp >= NOW() - INTERVAL '%s days'
                        GROUP BY c.channel_id, c.channel_name
                    """, (f'%{channel_name}%', days))
                else:
                    cur.execute("""
                        SELECT 
                            c.channel_name,
                            COUNT(r.id) as reading_count,
                            ROUND(AVG(r.power_kw)::numeric, 2) as avg_power_kw,
                            ROUND(SUM(r.energy_kwh)::numeric, 2) as total_energy_kwh
                        FROM channels c
                        LEFT JOIN readings r ON c.channel_id = r.channel_id
                        WHERE r.timestamp >= NOW() - INTERVAL '%s days'
                        GROUP BY c.channel_id, c.channel_name
                        ORDER BY total_energy_kwh DESC NULLS LAST
                        LIMIT 10
                    """, (days,))
                
                return self._format_table(cur.fetchall())
    
    def get_total_energy(self, days=7):
        """Get total energy consumption"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        COUNT(DISTINCT channel_id) as channels,
                        COUNT(*) as readings,
                        ROUND(SUM(energy_kwh)::numeric, 2) as total_kwh,
                        ROUND(AVG(power_kw)::numeric, 2) as avg_power_kw,
                        MIN(timestamp) as period_start,
                        MAX(timestamp) as period_end
                    FROM readings
                    WHERE timestamp >= NOW() - INTERVAL '%s days'
                """, (days,))
                
                result = cur.fetchone()
                if result:
                    return f"""
📊 Energy Summary (Last {days} days)
{'=' * 50}
Channels:        {result['channels']}
Total Readings:  {result['readings']:,}
Total Energy:    {result['total_kwh']:,.2f} kWh
Average Power:   {result['avg_power_kw']:.2f} kW
Period:          {result['period_start']} to {result['period_end']}
"""
                return "No data found"
    
    def get_top_consumers(self, days=7, limit=10):
        """Get top energy consumers"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        c.channel_name,
                        ROUND(SUM(r.energy_kwh)::numeric, 2) as total_kwh,
                        ROUND(AVG(r.power_kw)::numeric, 2) as avg_kw,
                        ROUND(MAX(r.power_kw)::numeric, 2) as peak_kw
                    FROM channels c
                    JOIN readings r ON c.channel_id = r.channel_id
                    WHERE r.timestamp >= NOW() - INTERVAL '%s days'
                    GROUP BY c.channel_id, c.channel_name
                    ORDER BY total_kwh DESC
                    LIMIT %s
                """, (days, limit))
                
                return self._format_table(cur.fetchall())
    
    def get_hourly_pattern(self, channel_name=None, days=7):
        """Get hourly consumption pattern"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                if channel_name:
                    cur.execute("""
                        SELECT 
                            EXTRACT(HOUR FROM r.timestamp) as hour,
                            ROUND(AVG(r.power_kw)::numeric, 2) as avg_power_kw,
                            COUNT(*) as readings
                        FROM readings r
                        JOIN channels c ON r.channel_id = c.channel_id
                        WHERE c.channel_name ILIKE %s
                            AND r.timestamp >= NOW() - INTERVAL '%s days'
                        GROUP BY EXTRACT(HOUR FROM r.timestamp)
                        ORDER BY hour
                    """, (f'%{channel_name}%', days))
                else:
                    cur.execute("""
                        SELECT 
                            EXTRACT(HOUR FROM timestamp) as hour,
                            ROUND(AVG(power_kw)::numeric, 2) as avg_power_kw,
                            COUNT(*) as readings
                        FROM readings
                        WHERE timestamp >= NOW() - INTERVAL '%s days'
                        GROUP BY EXTRACT(HOUR FROM timestamp)
                        ORDER BY hour
                    """, (days,))
                
                return self._format_table(cur.fetchall())
    
    def get_recent_readings(self, channel_name=None, limit=20):
        """Get most recent readings"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                if channel_name:
                    cur.execute("""
                        SELECT 
                            r.timestamp,
                            c.channel_name,
                            ROUND(r.power_kw::numeric, 2) as power_kw,
                            ROUND(r.energy_kwh::numeric, 2) as energy_kwh
                        FROM readings r
                        JOIN channels c ON r.channel_id = c.channel_id
                        WHERE c.channel_name ILIKE %s
                        ORDER BY r.timestamp DESC
                        LIMIT %s
                    """, (f'%{channel_name}%', limit))
                else:
                    cur.execute("""
                        SELECT 
                            r.timestamp,
                            c.channel_name,
                            ROUND(r.power_kw::numeric, 2) as power_kw,
                            ROUND(r.energy_kwh::numeric, 2) as energy_kwh
                        FROM readings r
                        JOIN channels c ON r.channel_id = c.channel_id
                        ORDER BY r.timestamp DESC
                        LIMIT %s
                    """, (limit,))
                
                return self._format_table(cur.fetchall())
    
    def search_channels(self, search_term):
        """Search for channels by name"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        channel_id,
                        channel_name,
                        channel_type,
                        (SELECT COUNT(*) FROM readings WHERE channel_id = c.channel_id) as total_readings
                    FROM channels c
                    WHERE channel_name ILIKE %s
                    ORDER BY channel_name
                """, (f'%{search_term}%',))
                
                return self._format_table(cur.fetchall())
    
    def query(self, question):
        """Parse natural language question and route to appropriate query"""
        q = question.lower()
        
        # Extract channel name if mentioned
        channel_name = None
        for word in question.split():
            if len(word) > 3 and not word.lower() in ['show', 'what', 'list', 'get', 'find', 'total', 'average']:
                # Check if this might be a channel name
                with self._get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT channel_name FROM channels WHERE channel_name ILIKE %s LIMIT 1", (f'%{word}%',))
                        result = cur.fetchone()
                        if result:
                            channel_name = word
                            break
        
        # Route based on keywords
        if 'list' in q and 'channel' in q:
            return self.list_channels()
        
        elif 'search' in q or 'find channel' in q:
            if channel_name:
                return self.search_channels(channel_name)
            return "Please specify a channel name to search for"
        
        elif 'total' in q and 'energy' in q:
            days = 7
            if 'week' in q:
                days = 7
            elif 'month' in q:
                days = 30
            elif 'today' in q:
                days = 1
            return self.get_total_energy(days)
        
        elif 'top' in q or 'highest' in q or 'most' in q:
            days = 7
            if 'month' in q:
                days = 30
            return self.get_top_consumers(days)
        
        elif 'hourly' in q or 'pattern' in q or 'by hour' in q:
            days = 7
            if 'month' in q:
                days = 30
            return self.get_hourly_pattern(channel_name, days)
        
        elif 'recent' in q or 'latest' in q or 'last reading' in q:
            return self.get_recent_readings(channel_name)
        
        elif 'stats' in q or 'statistics' in q or 'average' in q or 'summary' in q:
            days = 7
            if 'month' in q:
                days = 30
            elif 'week' in q:
                days = 7
            return self.get_channel_stats(channel_name, days)
        
        else:
            return """
❓ I'm not sure what you're asking. Try questions like:

📋 Data Overview:
   • "list all channels"
   • "show me total energy this week"
   • "show me total energy this month"

🔍 Channel Information:
   • "search for RTU"
   • "find channel Wilson"
   • "stats for RTU-1"
   • "average power for AHU-1A"

📊 Analysis:
   • "top energy consumers"
   • "top consumers this month"
   • "hourly pattern"
   • "hourly pattern for RTU-1"

⏱️ Recent Data:
   • "recent readings"
   • "latest readings for Dryer"

Examples:
   python query_energy_data.py "list all channels"
   python query_energy_data.py "show me total energy this week"
   python query_energy_data.py "top 10 consumers"
   python query_energy_data.py "stats for RTU-1"
   python query_energy_data.py "hourly pattern for AHU-2"
"""


def main():
    if len(sys.argv) < 2:
        print("""
🔍 Energy Data Query Tool

Usage:
    python query_energy_data.py "your question here"

Examples:
    python query_energy_data.py "list all channels"
    python query_energy_data.py "show me total energy this week"
    python query_energy_data.py "top energy consumers"
    python query_energy_data.py "stats for RTU-1"
    python query_energy_data.py "hourly pattern"
    python query_energy_data.py "recent readings for Dryer"

Try it now!
""")
        sys.exit(1)
    
    question = " ".join(sys.argv[1:])
    
    print(f"\n❓ Question: {question}\n")
    
    try:
        querier = EnergyDataQuery()
        result = querier.query(question)
        print(result)
        print()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
