# newsData_agent.py
import os
from dotenv import load_dotenv
from typing import Dict, List
from newsapi import NewsApiClient
from groq import Groq
from datetime import datetime, timedelta

load_dotenv()

class NewsDataAgent:
    def __init__(self):
        self.newsapi = NewsApiClient(api_key=os.environ["NEWS_API_KEY"])
        self.groq = Groq(api_key=os.environ["GROQ_API_KEY"])
        self.model = "mixtral-8x7b-32768"

    async def fetch_competitor_news(self, competitor: str, days_back: int = 30) -> List[Dict]:
        try:
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            news = self.newsapi.get_everything(
                q=f'"{competitor}" AND (software OR SaaS OR technology)',
                language='en',
                from_param=from_date,
                sort_by='relevancy'
            )
            return news['articles'][:10]
        except Exception as e:
            return [{"error": f"Error fetching news for {competitor}: {str(e)}"}]

    def analyze_competitor_news(self, competitor: str, news_articles: List[Dict]) -> Dict:
        try:
            news_text = "\n".join([
                f"Title: {article['title']}\nDescription: {article['description']}"
                for article in news_articles if article.get('title') and article.get('description')
            ])

            analysis = self.groq.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": """You are a preliminary research analyst preparing data for a main researcher. 
                    Analyze competitor news and provide factual, objective insights that will be used in a final research report. Focus on:
                    1. Recent product launches and feature updates (with dates if available)
                    2. Market positioning changes and target segments
                    3. Business strategy shifts and partnerships
                    4. Concrete growth indicators (revenue, user base, market share)
                    5. Identified challenges and risks
                    Format in clear bullet points with source references when possible."""},
                    {"role": "user", "content": f"Analyze these news articles about {competitor} to support the main research report:\n{news_text}"}
                ],
                temperature=0.2,  # Reduced for more factual output
                max_tokens=1000
            )

            return {
                "competitor": competitor,
                "news_count": len(news_articles),
                "analysis": analysis.choices[0].message.content,
                "recent_headlines": [article['title'] for article in news_articles[:5]],
                "analysis_date": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Error analyzing news for {competitor}: {str(e)}"}

    async def get_competitor_data(self, competitors: List[str]) -> Dict:
        results = {}
        for competitor in competitors:
            news = await self.fetch_competitor_news(competitor)
            analysis = self.analyze_competitor_news(competitor, news)
            results[competitor] = analysis
        return results

async def main():
    agent = NewsDataAgent()
    competitors = ["Salesforce", "HubSpot", "Zendesk"]
    data = await agent.get_competitor_data(competitors)
    print(data)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())