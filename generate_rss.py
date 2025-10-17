#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import re

def fetch_ijgis_articles():
    """抓取IJGIS最新文章"""
    url = "https://www.tandfonline.com/toc/tgis20/current"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        articles = []
        
        # 查找所有文章条目
        article_items = soup.find_all('div', class_='art_title')
        
        for item in article_items[:20]:  # 只取最新20篇
            try:
                # 提取标题和链接
                title_tag = item.find('a')
                if not title_tag:
                    continue
                    
                title = title_tag.get_text(strip=True)
                link = "https://www.tandfonline.com" + title_tag.get('href', '')
                
                # 获取文章详情页以提取摘要
                abstract = fetch_article_abstract(link, headers)
                
                # 查找作者信息
                authors = []
                author_section = item.find_next('div', class_='art_authors')
                if author_section:
                    author_links = author_section.find_all('a')
                    authors = [a.get_text(strip=True) for a in author_links]
                
                # 查找发布日期
                pub_date = None
                date_section = item.find_next('div', class_='art-pub-date')
                if date_section:
                    date_text = date_section.get_text(strip=True)
                    pub_date = parse_date(date_text)
                
                articles.append({
                    'title': title,
                    'link': link,
                    'abstract': abstract,
                    'authors': ', '.join(authors) if authors else 'Unknown',
                    'pub_date': pub_date or datetime.now()
                })
                
            except Exception as e:
                print(f"Error processing article: {e}")
                continue
        
        return articles
        
    except Exception as e:
        print(f"Error fetching articles: {e}")
        return []

def fetch_article_abstract(url, headers):
    """从文章页面抓取摘要"""
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 查找摘要部分
        abstract_section = soup.find('div', class_='abstractSection')
        if abstract_section:
            abstract_text = abstract_section.get_text(strip=True)
            # 移除"Abstract"标题
            abstract_text = re.sub(r'^Abstract[:\s]*', '', abstract_text, flags=re.IGNORECASE)
            return abstract_text[:500] + '...' if len(abstract_text) > 500 else abstract_text
        
        # 备选方案：查找meta标签中的描述
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content')
        
        return "No abstract available."
        
    except Exception as e:
        print(f"Error fetching abstract from {url}: {e}")
        return "Abstract unavailable."

def parse_date(date_string):
    """解析日期字符串"""
    try:
        # 尝试多种日期格式
        formats = [
            '%d %b %Y',
            '%B %d, %Y',
            'Published online: %d %b %Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        # 如果都失败，返回当前时间
        return datetime.now()
    except:
        return datetime.now()

def generate_rss_feed(articles):
    """生成RSS Feed"""
    fg = FeedGenerator()
    fg.title('International Journal of Geographical Information Science (IJGIS)')
    fg.link(href='https://www.tandfonline.com/toc/tgis20/current', rel='alternate')
    fg.description('Latest articles from IJGIS with full abstracts')
    fg.language('en')
    fg.id('https://www.tandfonline.com/toc/tgis20')
    
    for article in articles:
        fe = fg.add_entry()
        fe.title(article['title'])
        fe.link(href=article['link'])
        fe.description(f"<strong>Authors:</strong> {article['authors']}<br><br><strong>Abstract:</strong> {article['abstract']}")
        fe.guid(article['link'], permalink=True)
        fe.pubDate(article['pub_date'])
    
    # 保存为XML文件
    fg.rss_file('feed.xml', pretty=True)
    print(f"RSS feed generated successfully with {len(articles)} articles")

if __name__ == '__main__':
    print("Fetching IJGIS articles...")
    articles = fetch_ijgis_articles()
    
    if articles:
        print(f"Found {len(articles)} articles")
        generate_rss_feed(articles)
    else:
        print("No articles found")
