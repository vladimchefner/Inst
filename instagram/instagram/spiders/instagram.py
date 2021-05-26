import scrapy
import json
import re
from ..items import InstaPostItem


class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['www.instagram.com', 'i.instagram.com']
    start_urls = ['https://www.instagram.com/']
    _authorization_url = "https://www.instagram.com/accounts/login/ajax/"
    _tag_path = "/explore/tags/"
    _pag_url = "https://i.instagram.com/api/v1/tags/"

    def __init__(self, login, password, tag, **kwargs):
        super().__init__(**kwargs)
        self.login = login
        self.password = password
        self.tag = tag

    def parse(self, response, **kwargs):
        try:
            js_data = self.get_json_data(response)
            yield scrapy.FormRequest(
                self._authorization_url,
                method='POST',
                callback=self.parse,
                formdata={"username": self.login, "enc_password": self.password},
                headers={"X-CSRFToken": js_data['config']['csrf_token']}
            )
        except AttributeError:
            yield response.follow(f'{self._tag_path}{self.tag}/', callback=self.first_page_parse)

    @staticmethod
    def get_json_data(response):
        script = response.xpath("//script[contains(text(), 'window._sharedData = ')]/text()").get()
        return json.loads(script.replace('window._sharedData = ', '')[:-1])

    def first_page_parse(self, response):
        js_data = self.get_json_data(response)
        sections = js_data['entry_data']['TagPage'][0]['data']['recent']
        yield from self.parse_template(sections)

    def next_page_parse(self, response):
        js_data = response.json()
        yield from self.parse_template(js_data)

    def parse_template(self, sections):
        for section in sections['sections']:
            for post_data in section['layout_content']['medias']:
                yield self.post_data_parse(post_data['media'])
        if sections['more_available']:
            yield scrapy.FormRequest(
                f"{self._pag_url}{self.tag}/sections/",
                method="POST",
                callback=self.next_page_parse,
                formdata={"include_persistent": "0", "max_id": sections['next_max_id'],
                          "page": str(sections['next_page']), "surface": "grid", "tab": "recent"}
            )

    @staticmethod
    def post_data_parse(post_data):
        item = InstaPostItem()
        item['user_id'] = post_data['user']['pk']
        item['user_name'] = post_data['user']['username']
        try:
            text = post_data['caption']['text']
            item['hashtags'] = re.findall(r'[#]\w+', text)
        except TypeError:
            item['hashtags'] = []
        item['likes'] = post_data['like_count']
        return item
