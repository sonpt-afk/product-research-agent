# main_writer.py
import os
from typing import List, Dict
import requests
import asyncio
from datetime import datetime, timedelta
from groq import Groq
from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT

class MainWriterAgent:
    def __init__(self):
        load_dotenv()
        self.producthunt_token = os.environ.get("PRODUCTHUNT_TOKEN")
        if not self.producthunt_token:
            raise ValueError("PRODUCTHUNT_TOKEN not found in environment variables")
        self.client = Groq(api_key=os.environ["GROQ_API_KEY"])
        self.model = "mixtral-8x7b-32768"

    async def fetch_product_hunt_data(self, days_back: int = 30) -> List[Dict]:
        """Fetch recent SaaS launches from ProductHunt"""
        headers = {
            'Authorization': f'Bearer {self.producthunt_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        
        query = """
        {
          posts(first: 20, order: RANKING) {
            edges {
              node {
                name
                description
                tagline
                url
                votesCount
                website
                topics {
                  edges {
                    node {
                      name
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        try:
            response = requests.post(
                'https://api.producthunt.com/v2/api/graphql',
                headers=headers,
                json={'query': query}
            )
            data = response.json()
            saas_products = [
                edge['node'] for edge in data['data']['posts']['edges']
                if any('saas' in topic['node']['name'].lower() 
                      for topic in edge['node']['topics']['edges'])
            ]
            return saas_products
        except Exception as e:
            return [{"error": f"Error fetching ProductHunt data: {str(e)}"}]

    def export_to_pdf(self, products: List[Dict]) -> str:
        """Export product data to PDF"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        current_dir = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(current_dir, f"saas_product_report_{timestamp}.pdf")

        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=8
        )

        story = []
        
        # Title and Date
        story.append(Paragraph("SaaS Product Launch Report", title_style))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", styles["Normal"]))
        story.append(Spacer(1, 30))

        # Products
        for product in products:
            story.append(Paragraph(product['name'], heading_style))
            story.append(Paragraph(f"<b>Tagline:</b> {product['tagline']}", body_style))
            story.append(Paragraph(f"<b>Description:</b> {product['description']}", body_style))
            story.append(Paragraph(f"<b>Votes:</b> {product['votesCount']}", body_style))
            story.append(Paragraph(f"<b>Website:</b> <a href='{product['website']}' color='blue' underline='1'>Click here</a>", body_style))
            
            categories = ', '.join(edge['node']['name'] for edge in product['topics']['edges'])
            story.append(Paragraph(f"<b>Categories:</b> {categories}", body_style))
            story.append(Spacer(1, 20))

        doc.build(story)
        return filename

async def main():
    agent = MainWriterAgent()
    products = await agent.fetch_product_hunt_data()
    pdf_path = agent.export_to_pdf(products)
    print(f"Report generated and saved to: {pdf_path}")

if __name__ == "__main__":
    asyncio.run(main())