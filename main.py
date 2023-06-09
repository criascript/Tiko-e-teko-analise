from bs4 import BeautifulSoup
import re
import requests
from fastapi import FastAPI

app = FastAPI()
class TikTokUser:
    """
    Main Class of The Scrapy
    """
    def __init__(self, username: str):
        self.username = username
        self.data = {}
        self.kpis = {}

    def calculate_kpis(self):
        """
        Calculates KPIs for the TikTok user specified by the username.
        """
        monetization_views_remaining: float = 100_000 - self.data["views"] 
        monetization_views_remaining = monetization_views_remaining if monetization_views_remaining > 0 else 0

        monetization_followers_remaining: float = 10_000 - self.data["followers"]
        monetization_followers_remaining = monetization_followers_remaining if monetization_followers_remaining > 0 else 0

        monetization_views_percentage_completed: float = min(100, self.data["views"] / 1000)
        monetization_followers_percentage_completed: float = min(100, self.data["followers"] / 100)

        views_per_video: float = self.data["views"] / len(self.data["videos"])
        likes_per_video: float = self.data["likes"] / len(self.data["videos"])

        likes_per_view: float = self.data["likes"] / self.data["views"]
        followers_per_view: float = self.data["followers"] / self.data["views"]

        self.data["KPIs"] = {
              "monetization_views_remaining": monetization_views_remaining,
              "monetization_followers_remaining":  monetization_followers_remaining,
              "monetization_views_percentage_completed": monetization_views_percentage_completed,
              "monetization_followers_percentage_completed": monetization_followers_percentage_completed,
              "views/video":  views_per_video,
              "likes/video": likes_per_video,
              "likes/views": likes_per_view,
              "followers/views": followers_per_view
          }
        
    @staticmethod
    def parse_count(data):
      """
      Convert data with abreviation K or M in float numbers
      Example: 1k => 1000.0, 1M => 1000000.0 
      """
      if re.match(r'^\d+(\.\d+)?[Kk]$', data):
        return float(data[:-1]) * 1000
      if re.match(r'^\d+(\.\d+)?[Mm]$', data):
        return float(data[:-1]) * 1000000
      return float(data or 0)

    def get_data(self):
        """
        Fetches data for the TikTok user specified by the username.
        """
        url: str = f"https://www.tiktok.com/@{self.username}"
        try:
            response: requests.Response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            raise error

        soup: BeautifulSoup = BeautifulSoup(response.text, 'html.parser')

        # Support integer, K and M
        following = int(self.parse_count(soup.find('strong', {'data-e2e': 'following-count'}).text))
        followers = int(self.parse_count(soup.find('strong', {'data-e2e': 'followers-count'}).text))
        likes =  int(self.parse_count(soup.find('strong', {'data-e2e': 'likes-count'}).text))
        views: list[BeautifulSoup] = soup.find_all('strong', {'class': 'video-count', 'data-e2e': 'video-views'})
        views_values: list[int] = [ int(self.parse_count(view.text)) for view in views]

        # for now, this get just the last 16 posts. 
        user_posts: list[BeautifulSoup] = soup.find_all(attrs={"data-e2e": "user-post-item-desc"})

        list_titles: list[str] = []

        for post in user_posts:
            a_tags: list[BeautifulSoup] = post.find_all('a')
            title = [a_tag.text for a_tag in a_tags][0]
            list_titles.append(title)

        dict_videos: Dict[str, int] = dict(zip(list_titles, views_values))

        self.data = {
            "following": following,
            "followers": followers,
            "likes": likes,
            "views": sum(views_values),
            "videos": dict_videos
        }

        self.calculate_kpis()

        return self.data

@app.get('/{username}')
def get_user_data(username: str):
   """
   Get the user assingment in the url and call method TikTokUser to scrapy her info's and return in Json to the WebAPI
   """
   user = TikTokUser(username)
   return user.get_data()

