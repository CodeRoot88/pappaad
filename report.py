from google.ads.googleads.client import GoogleAdsClient
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional


class GoogleAdsReportIntegration:
    """Integration class for fetching various Google Ads reports."""

    def __init__(self, client: GoogleAdsClient, googleads_account_id: str, campaign_id: Optional[int] = None):
        self.client = client
        self.googleads_account_id = googleads_account_id
        self.campaign_id = campaign_id
        self._ads_service = None

    @property
    def ads_service(self):
        """Lazy loading of Google Ads service."""
        if not self._ads_service:
            self._ads_service = self.client.get_service("GoogleAdsService")
        return self._ads_service

    def _execute_query(self, query: str) -> Any:
        """Execute a GAQL query and return the response."""
        return self.ads_service.search_stream(customer_id=self.googleads_account_id, query=query)

    def _format_date_range(self, days: int = 30) -> Tuple[str, str]:
        """Return formatted start and end dates for queries."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

    def _calculate_metrics(self, row: Any) -> Dict[str, float]:
        """Calculate common metrics from a result row."""
        cost = row.metrics.cost_micros / 1e6
        conversions = row.metrics.conversions
        clicks = row.metrics.clicks
        impressions = row.metrics.impressions

        return {
            "impressions": impressions,
            "clicks": clicks,
            "cost": cost,
            "conversions": conversions,
            "ctr": clicks / impressions if impressions > 0 else 0,
            "cvr": conversions / clicks if clicks > 0 else 0,
        }

    def _build_date_filter(self, start_date: str, end_date: str) -> str:
        """Build a date filter clause for queries."""
        return f"segments.date BETWEEN '{start_date}' AND '{end_date}'"

    def _process_performance_row(self, row: Any) -> Tuple:
        """Process a row for performance report."""
        metrics = self._calculate_metrics(row)
        return (
            row.segments.date,
            metrics["clicks"],
            metrics["impressions"],
            metrics["conversions"],
            metrics["cost"] / metrics["clicks"] if metrics["clicks"] > 0 else 0,
            metrics["cost"],
        )

    def performance_report(self) -> str:
        """Fetch performance report for the last month."""
        start_date, end_date = self._format_date_range()
        date_filter = self._build_date_filter(start_date, end_date)

        query = f"""
        SELECT
            metrics.clicks,
            metrics.impressions,
            metrics.conversions,
            metrics.cost_micros,
            segments.date
        FROM campaign
        WHERE {date_filter}
        """

        if self.campaign_id:
            query += f" AND campaign.id = {self.campaign_id}"

        results = [["date", "clicks", "impressions", "conversions", "cost_per_click", "cost"]]
        for batch in self._execute_query(query):
            for row in batch.results:
                results.append(self._process_performance_row(row))

        return "\n".join([",".join(map(str, row)) for row in results])

    def _process_keyword_row(self, row: Any, include_group: bool = True) -> Dict[str, Any]:
        """Process a row for keyword reports."""
        base_data = {
            "campaign_id": row.campaign.id,
            "campaign_name": row.campaign.name,
            "keyword": row.ad_group_criterion.keyword.text,
        }

        if include_group:
            base_data.update(
                {
                    "ad_group_id": row.ad_group.id,
                    "ad_group_name": row.ad_group.name,
                    "keyword_id": row.ad_group_criterion.criterion_id,
                    "match_type": row.ad_group_criterion.keyword.match_type,
                }
            )

        return {**base_data, **self._calculate_metrics(row)}

    def keyword_performance_report(self, include_groups: bool = True) -> List[Dict[str, Any]]:
        """Fetch keyword performance report with configurable group inclusion."""
        group_fields = (
            """
            ad_group.id,
            ad_group.name,
            ad_group_criterion.criterion_id,
            ad_group_criterion.keyword.match_type,
        """
            if include_groups
            else ""
        )

        query = f"""
        SELECT
            campaign.id,
            campaign.name,
            {group_fields}
            ad_group_criterion.keyword.text,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions
        FROM keyword_view
        WHERE segments.date DURING LAST_30_DAYS 
        AND metrics.conversions > 0
        ORDER BY metrics.impressions DESC
        LIMIT 50
        """

        results = []
        for batch in self._execute_query(query):
            for row in batch.results:
                results.append(self._process_keyword_row(row, include_groups))
        return results

    def ad_group_keyword_performance_report(self) -> List[Dict[str, Any]]:
        """Fetch keyword performance for ad groups."""
        return self.keyword_performance_report(include_groups=True)

    def campaign_keyword_performance_report(self) -> List[Dict[str, Any]]:
        """Fetch keyword performance for campaigns."""
        return self.keyword_performance_report(include_groups=False)

    def get_top_performing_url(self) -> Optional[str]:
        """Fetch the top performing URL based on conversions."""
        query = """
        SELECT
            ad_group_ad.final_urls,
            metrics.clicks,
            metrics.conversions,
            metrics.cost_micros
        FROM ad_group_ad
        WHERE segments.date DURING LAST_30_DAYS
        ORDER BY metrics.conversions DESC
        LIMIT 1
        """

        for batch in self._execute_query(query):
            for row in batch.results:
                return row.ad_group_ad.final_urls[0]
        return None

    def ad_group_keyword_performance_by_week(self, ad_group_id: str, weeks: int = 6) -> List[Dict[str, Any]]:
        """Fetch keyword performance data for a specific ad group over time."""
        start_date, end_date = self._format_date_range(days=weeks * 7)
        date_filter = self._build_date_filter(start_date, end_date)

        query = f"""
        SELECT
            segments.date,
            ad_group_criterion.keyword.text,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions
        FROM keyword_view
        WHERE 
            ad_group.id = {ad_group_id}
            AND {date_filter}
        ORDER BY segments.date DESC
        """

        # query = f"""
        # SELECT
        #     ad_group.id
        # FROM ad_group
        # WHERE
        #     ad_group.id = {ad_group_id}
        # """
        results = []
        for batch in self._execute_query(query):
            for row in batch.results:
                results.append(
                    {
                        "date": row.segments.date,
                        "keyword": row.ad_group_criterion.keyword.text,
                        **self._calculate_metrics(row),
                    }
                )
        return results
